# ai-generated: 90% - implemented the Lab 5 SARIF matching and confusion-matrix rules
"""Compute per-tool confusion matrices from SARIF findings and labelled defects."""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


CLASSES_BY_CWE = {
    "secret": {259, 260, 321, 798},
    "injection": {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    "deserialization": {502},
    "weak-crypto": {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    "insecure-transport": {295, 297, 319, 322, 757},
    "path-traversal": {22, 23, 35, 36, 73},
    "ssrf": {918},
    "vulnerable-dependency": {937, 1035, 1104, 1395},
    "misconfiguration": {16, 215, 250, 489, 668, 732, 1188},
    "access-control": {284, 285, 639, 862, 863},
}
CLASS_NAMES = set(CLASSES_BY_CWE)
CWE_CLASSES = {
    cwe: class_name
    for class_name, cwes in CLASSES_BY_CWE.items()
    for cwe in cwes
}
CWE_PATTERN = re.compile(r"(?<![A-Za-z0-9])CWE-(\d+)", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
PEP503_PATTERN = re.compile(r"[-_.]+")
SEMgrep_NAMES = {
    "semgrep",
    "semgrep ce",
    "semgrep community edition",
    "semgrep oss",
    "semgrep pro",
}


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _tool_id(run: dict) -> str:
    driver = _dict(_dict(run.get("tool")).get("driver"))
    name = driver.get("name")
    if not isinstance(name, str) or not name.strip():
        return "unknown"
    normalized = name.strip().lower()
    if normalized in {"trivy", "grype", "osv-scanner", "gitleaks"}:
        return normalized
    if normalized in SEMgrep_NAMES:
        return "semgrep"
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "unknown"


def _is_empty(value: object) -> bool:
    return value is None or value is False or value == 0 or value == "" or value == [] or value == {}


def _result_location(result: dict) -> tuple[str | None, int | None, int | None]:
    locations = _list(result.get("locations"))
    if not locations:
        return None, None, None
    physical = _dict(_dict(locations[0]).get("physicalLocation"))
    artifact = _dict(physical.get("artifactLocation"))
    uri = artifact.get("uri")
    if not isinstance(uri, str) or not uri:
        return None, None, None

    path = unquote(uri, encoding="utf-8", errors="replace")
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    components = path.split("/")
    root = _current_set_root
    matches = [index for index, component in enumerate(components) if component == root]
    if not matches:
        return None, None, None
    file_path = "/".join(components[matches[-1]:])

    region = _dict(physical.get("region"))
    start = region.get("startLine")
    if type(start) is not int or start < 1:
        return file_path, None, None
    end = region.get("endLine")
    if type(end) is not int or end < start:
        end = start
    return file_path, start, end


def _normalise_cwe_tags(tags: list) -> set[str]:
    found = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        for match in CWE_PATTERN.finditer(tag):
            class_name = CWE_CLASSES.get(int(match.group(1)))
            if class_name:
                found.add(class_name)
    return found


def _result_classes(tool: str, result: dict, rule: dict | None) -> set[str]:
    result_properties = _dict(result.get("properties"))
    direct_class = result_properties.get("class")
    if isinstance(direct_class, str) and direct_class in CLASS_NAMES:
        return {direct_class}

    rule_properties = _dict(_dict(rule).get("properties"))
    rule_tags = [tag for tag in _list(rule_properties.get("tags")) if isinstance(tag, str)]
    result_tags = [tag for tag in _list(result_properties.get("tags")) if isinstance(tag, str)]

    if tool == "gitleaks":
        return {"secret"}
    if tool in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if tool == "trivy":
        trivy_classes = {
            "vulnerability": "vulnerable-dependency",
            "secret": "secret",
            "misconfiguration": "misconfiguration",
        }
        from_rule_tags = {
            trivy_classes[tag.lower()]
            for tag in rule_tags
            if tag.lower() in trivy_classes
        }
        if from_rule_tags:
            return from_rule_tags

    return _normalise_cwe_tags(result_tags + rule_tags) or {"other"}


def _rule_index(run: dict) -> dict[str, dict]:
    driver = _dict(_dict(run.get("tool")).get("driver"))
    rules = {}
    for rule in _list(driver.get("rules")):
        if isinstance(rule, dict) and isinstance(rule.get("id"), str):
            rules.setdefault(rule["id"], rule)
    return rules


def _dependency_tokens(message: object) -> set[str]:
    text = _dict(message).get("text")
    if not isinstance(text, str):
        return set()
    tokens = set()
    for match in TOKEN_PATTERN.findall(text):
        token = match.strip("._-")
        if token:
            tokens.add(PEP503_PATTERN.sub("-", token.lower()))
    return tokens


_current_set_root = ""


def _analysis_result(result: dict, tool: str, rules: dict[str, dict]) -> dict | None:
    if result.get("kind") not in (None, "fail"):
        return None
    suppressions = result.get("suppressions")
    if not _is_empty(suppressions):
        return None

    file_path, start, end = _result_location(result)
    if file_path is None:
        return None
    rule_id = result.get("ruleId")
    rule = rules.get(rule_id) if isinstance(rule_id, str) else None
    return {
        "file": file_path,
        "start": start,
        "end": end,
        "rule_id": rule_id if isinstance(rule_id, str) else None,
        "classes": _result_classes(tool, result, rule),
        "tokens": _dependency_tokens(result.get("message")),
    }


def _matches(result: dict, defect: dict) -> bool:
    if result["file"] != defect.get("file") or defect.get("class") not in result["classes"]:
        return False
    if defect.get("class") == "vulnerable-dependency":
        package = defect.get("package")
        if not isinstance(package, str):
            return False
        normalized = PEP503_PATTERN.sub("-", package.lower())
        return normalized in result["tokens"]
    start, end = result["start"], result["end"]
    defect_start, defect_end = defect.get("start_line"), defect.get("end_line")
    return (
        start is not None
        and end is not None
        and type(defect_start) is int
        and type(defect_end) is int
        and start <= defect_end
        and defect_start <= end
    )


def confusion_matrix(labels: dict, sarif_documents: list[dict]) -> dict:
    """Return the Lab 5 per-tool confusion matrix for P-14 through P-22."""
    global _current_set_root
    _current_set_root = labels["set"]
    defects = labels["defects"]
    by_tool: dict[str, list[dict]] = {}

    for document in sarif_documents:
        for run in _list(_dict(document).get("runs")):
            if not isinstance(run, dict):
                continue
            tool = _tool_id(run)
            results = by_tool.setdefault(tool, [])
            rules = _rule_index(run)
            for result in _list(run.get("results")):
                if isinstance(result, dict):
                    analyzed = _analysis_result(result, tool, rules)
                    if analyzed is not None:
                        results.append(analyzed)

    tools = {}
    for tool in sorted(by_tool):
        found_defects = set()
        false_positives = set()
        for result in by_tool[tool]:
            matched = {
                index
                for index, defect in enumerate(defects)
                if _matches(result, defect)
            }
            if matched:
                found_defects.update(matched)
            else:
                false_positives.add(
                    (result["rule_id"], result["file"], result["start"], result["end"])
                )
        tp = len(found_defects)
        fp = len(false_positives)
        fn = len(defects) - tp
        precision = round(tp / (tp + fp), 4) if tp + fp else None
        recall = round(tp / (tp + fn), 4) if tp + fn else None
        f1_denominator = 2 * tp + fp + fn
        f1 = round(2 * tp / f1_denominator, 4) if f1_denominator else None
        tools[tool] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {"set": labels["set"], "defects": len(defects), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)"
    )
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8") as fh:
        labels = json.load(fh)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as fh:
            documents.append(json.load(fh))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
