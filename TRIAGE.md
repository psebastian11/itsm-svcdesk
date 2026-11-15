---
lab5_triage:
  image: ghcr.io/psebastian11/itsm-svcdesk@sha256:5164252aa2f5abfb15ba273c798a967c2920bdf62502238552ee7b8f1d8cd0e6
  sarif_receipt: 428
---
<!-- ai-generated: 90% - drafted triage decisions from the receipted SARIF and measured bake-off -->
# Triage

What the gates and the reporting scanners found on my service, and what I did about each (CI-SPEC.md P-11, P-12).
One row per rule of one tool; a row may cover several locations, and the Reason says which. Tool is the tool id of
P-15 (`trivy`, `grype`, `osv-scanner`, `gitleaks`, `semgrep`). Decision is one of `fix`, `ignore`,
`false-positive`, `accept`.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| semgrep | dockerfile.security.missing-user.missing-user | fix | Added the unprivileged `svcdesk` UID/GID 10001 in `Dockerfile`; the rebuilt image and service tests pass. |
| semgrep | python.lang.security.audit.insecure-transport.urllib.insecure-request-object.insecure-request-object | false-positive | `generate_gaming.py` sends its test request only to the loopback `http://localhost:8080` service; it is not an external transport. |
| semgrep | python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected | false-positive | In `generate_gaming.py`, the URL is a fixed loopback test endpoint. In `src/app.py`, `KB_INDEX_URL` is deployment configuration for the internal `kb-index` service; request input is only the URL-encoded query, and the upstream call has a three-second timeout. |

## Bake-off

The canary has 10 labelled defects. Gitleaks found 1 true positive, 0 false positives, and missed 9 (precision 1.00, recall 0.10); this is useful as a narrow blocking secret gate, not as a general security detector. Grype found 2, 0, and 8 respectively (precision 1.00, recall 0.20). OSV-Scanner also found 2, had 0 false positives, and missed 8 (precision 1.00, recall 0.20). Trivy found 2, had 0 false positives, and missed 8 (precision 1.00, recall 0.20); I would keep its dependency gate because it found both seeded dependency defects without a false alarm. Semgrep found the most canary defects: 4 true positives, 1 false positive, and 6 false negatives (precision 0.80, recall 0.40). Its stronger recall is useful for reporting, but the false positive argues for review before making every rule a blocking gate.

The matching dependency results from Grype, OSV-Scanner, and Trivy were less diverse than expected: all three detected the same two vulnerable packages and none of the application-level defects. No tool found A16 (the service-specific SSRF) or C04 and C05 (the two source-controlled secrets). These require understanding application behavior or recognizing secrets in context, unlike a known vulnerable package version, so the gap is a reminder that the scanners are complementary rather than interchangeable. Every recall here is only an upper bound: this is a small, deliberately seeded set, and its known patterns favor the detectors being compared. Unseeded defects, different frameworks, and production configurations could lower real-world recall.
