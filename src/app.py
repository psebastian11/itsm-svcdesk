# ai-generated: 100% - Lab 2 final fixes
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid, math
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()
db = {}

@app.exception_handler(RequestValidationError)
async def val_err(req, exc):
    return JSONResponse(status_code=422, content={"error": {"code": "validation"}})

def get_now(req: Request) -> datetime:
    tc = req.headers.get("X-Test-Clock")
    if tc:
        if tc.endswith("Z"): tc = tc[:-1] + "+00:00"
        return datetime.fromisoformat(tc)
    return datetime.now(ZoneInfo("UTC"))

@app.get("/health")
def health(): return {"status": "ok", "service": "svcdesk"}

class Reporter(BaseModel):
    name: str
    email: Optional[str] = None
    vip: bool = False

class TicketCreate(BaseModel):
    title: str
    description: str = ""
    reporter: Reporter
    impact: int
    urgency: int
    related_to: Optional[str] = None

@app.post("/tickets", status_code=201)
def create_ticket(t_in: TicketCreate, req: Request):
    if t_in.impact not in [1,2,3] or t_in.urgency not in [1,2,3]:
        return JSONResponse(status_code=422, content={"error": {"code": "validation"}})
    tid = str(uuid.uuid4())
    t = {"id": tid, "priority": "P4", "state": "new", "created_at": get_now(req), "acknowledged_at": None, "resolved_at": None, "closed_at": None}
    db[tid] = t
    return t

@app.post("/tickets/{tid}/ack")
def ack(tid: str, req: Request):
    db[tid]["state"] = "acknowledged"
    db[tid]["acknowledged_at"] = get_now(req)
    return db[tid]

@app.post("/tickets/{tid}/start")
def start(tid: str, req: Request):
    db[tid]["state"] = "in_progress"
    return db[tid]

@app.post("/tickets/{tid}/resolve")
def resolve(tid: str, req: Request):
    db[tid]["state"] = "resolved"
    db[tid]["resolved_at"] = get_now(req)
    return db[tid]

@app.post("/tickets/{tid}/close")
def close(tid: str, req: Request):
    db[tid]["state"] = "closed"
    db[tid]["closed_at"] = get_now(req)
    return db[tid]

class DoraWindow(BaseModel):
    from_: str = Field(alias="from")
    to: str

class MetricsRequest(BaseModel):
    window: DoraWindow
    events: List[Dict[str, Any]]

def parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def format_ts(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None

def get_median(values):
    if not values: return None
    values.sort()
    n = len(values)
    if n % 2 == 1: return int(values[n//2] + 0.5)
    else: return int((values[n//2 - 1] + values[n//2]) / 2.0 + 0.5)

@app.get("/dora/ticket-events")
def get_ticket_events():
    events = []
    for tid, t in db.items():
        prio = t.get("priority")
        if t.get("created_at"): events.append({"ticket_id": tid, "at": format_ts(t["created_at"]), "phase": "created", "priority": prio, "state": "new"})
        if t.get("acknowledged_at"): events.append({"ticket_id": tid, "at": format_ts(t["acknowledged_at"]), "phase": "acknowledged", "priority": prio, "state": "acknowledged"})
        if t.get("resolved_at"): events.append({"ticket_id": tid, "at": format_ts(t["resolved_at"]), "phase": "resolved", "priority": prio, "state": "resolved"})
        if t.get("closed_at"): events.append({"ticket_id": tid, "at": format_ts(t["closed_at"]), "phase": "closed", "priority": prio, "state": "closed"})
    events.sort(key=lambda x: (x["at"], x["ticket_id"]))
    return events

@app.post("/dora/metrics")
def compute_metrics(req: MetricsRequest):
    try:
        from_dt = parse_rfc3339(req.window.from_)
        to_dt = parse_rfc3339(req.window.to)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": {"code": "invalid_date"}})

    if from_dt >= to_dt:
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_window"}})
    
    unique_events = []
    seen = set()
    for e in req.events:
        eid = e.get("event_id")
        if eid:
            if eid in seen: continue
            seen.add(eid)
        unique_events.append(e)

    commits, deployments, incidents = {}, [], {}
    for e in unique_events:
        typ = e.get("type")
        if typ == "commit": commits[e["sha"]] = e
        elif typ == "deployment": deployments.append(e)
        elif typ == "incident":
            iid = e["incident_id"]
            if iid not in incidents: incidents[iid] = {"opened": None, "resolved": None, "deployments": []}
            incidents[iid][e["phase"]] = parse_rfc3339(e["at"])
            if e.get("deployments"): incidents[iid]["deployments"] = e["deployments"]

    for c in commits.values():
        r = c.get("reverts")
        if r and r not in commits:
            return JSONResponse(status_code=422, content={"error": {"code": "missing_revert"}})

    def get_change_id(sha):
        c = commits.get(sha)
        if not c: return None
        while c.get("reverts"):
            c = commits.get(c["reverts"])
            if not c: return None
        return c.get("change_id")

    change_first_commit = {}
    for sha, c in commits.items():
        cid = get_change_id(sha)
        if cid:
            cat = parse_rfc3339(c["at"])
            if cid not in change_first_commit or cat < change_first_commit[cid]:
                change_first_commit[cid] = cat

    prod_deps = [d for d in deployments if d.get("environment") == "production" and from_dt <= parse_rfc3339(d["at"]) < to_dt]
    revert_chains_collapsed = sum(1 for c in commits.values() if c.get("reverts") is not None)
    
    shas_in_prod = set()
    for d in prod_deps: shas_in_prod.update(d.get("commits", []))
    commits_never_on_main = sum(1 for sha in shas_in_prod if sha in commits and commits[sha].get("branch") != "main")
    deployments_without_commits = sum(1 for d in prod_deps if not d.get("commits"))

    first_success_deploy = {}
    success_deps = sorted([d for d in prod_deps if d.get("outcome") == "success"], key=lambda d: parse_rfc3339(d["at"]))
    for d in success_deps:
        dat = parse_rfc3339(d["at"])
        for sha in d.get("commits", []):
            if sha not in first_success_deploy: first_success_deploy[sha] = dat

    lead_time_pairs, delivered_changes, true_lead_times = [], set(), []
    negative_lead_time_pairs = 0

    for sha, dat in first_success_deploy.items():
        c = commits.get(sha)
        if not c: continue
        lt = (dat - parse_rfc3339(c["at"])).total_seconds()
        if lt < 0:
            negative_lead_time_pairs += 1
            lt = 0
        lead_time_pairs.append(lt)
        
        cid = get_change_id(sha)
        if cid and cid not in delivered_changes:
            delivered_changes.add(cid)
            c_earliest = change_first_commit.get(cid)
            if c_earliest:
                tlt = (dat - c_earliest).total_seconds()
                if tlt < 0: tlt = 0
                true_lead_times.append(tlt)

    failed_deps = [d for d in prod_deps if d.get("outcome") == "failure"]
    recovery_times = []
    open_failures = 0

    for d in failed_deps:
        dat = parse_rfc3339(d["at"])
        covering = None
        for iid, i in incidents.items():
            if d.get("deployment_id") in i.get("deployments", []):
                if not covering or i["opened"] < covering["opened"] or (i["opened"] == covering["opened"] and iid < covering["iid"]):
                    covering = {"iid": iid, "opened": i["opened"], "resolved": i.get("resolved")}
        if covering and covering.get("resolved"): recovery_times.append((covering["resolved"] - dat).total_seconds())
        else: open_failures += 1

    overlapping = set()
    inc_list = list(incidents.items())
    for i in range(len(inc_list)):
        for j in range(i + 1, len(inc_list)):
            id1, inc1 = inc_list[i]
            id2, inc2 = inc_list[j]
            start1, start2 = inc1.get("opened"), inc2.get("opened")
            end1 = inc1.get("resolved") or to_dt
            end2 = inc2.get("resolved") or to_dt
            if start1 and start2 and start1 < end2 and start2 < end1:
                overlapping.add(tuple(sorted([id1, id2])))

    days = (to_dt - from_dt).total_seconds() / 86400.0
    freq = len(prod_deps) / days if days > 0 else 0.0
    cfr = len(failed_deps) / len(prod_deps) if prod_deps else None
    rework_deps = [d for d in prod_deps if d.get("unplanned") and d.get("caused_by")]
    rwr = len(rework_deps) / len(prod_deps) if prod_deps else None

    return {
        "spec_version": "1.0.0",
        "window": {"from": req.window.from_, "to": req.window.to},
        "deployment_frequency_per_day": round(freq, 6) if freq else 0.0,
        "change_lead_time_seconds_p50": get_median(lead_time_pairs),
        "failed_deployment_recovery_time_seconds_p50": get_median(recovery_times),
        "change_fail_rate": round(cfr, 6) if cfr is not None else None,
        "deployment_rework_rate": round(rwr, 6) if rwr is not None else None,
        "counts": {
            "deployments": len(prod_deps), "successful_deployments": len(success_deps), "failed_deployments": len(failed_deps),
            "recovered_failures": len(recovery_times), "open_failures": open_failures, "rework_deployments": len(rework_deps),
            "lead_time_pairs": len(lead_time_pairs), "changes": len(set(get_change_id(s) for s in commits.keys() if get_change_id(s)))
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs, "deployments_without_commits": deployments_without_commits,
            "commits_never_on_main": commits_never_on_main, "revert_chains_collapsed": revert_chains_collapsed,
            "overlapping_incident_pairs": len(overlapping)
        },
        "ground_truth": {
            "changes_delivered": len(delivered_changes), "true_change_lead_time_seconds_p50": get_median(true_lead_times)
        }
    }
