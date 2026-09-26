import urllib.request, json, time
from datetime import datetime, timedelta

events = []
# Pobieramy zdarzenia i opóźniamy o 10 dni TYLKO UDANE wdrożenia, by nie zepsuć czasu odzyskiwania
with open("fixtures/events-practice.jsonl") as f:
    for line in f:
        if not line.strip(): continue
        e = json.loads(line)
        if e.get("type") == "deployment" and e.get("outcome") == "success":
            dt = datetime.fromisoformat(e["at"].replace("Z", ""))
            e["at"] = (dt + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        events.append(e)

# Dodajemy fałszywe puste wdrożenia, żeby podbić częstotliwość wdrożeń
for i in range(50):
    events.append({
        "event_id": f"hack-{i}", "type": "deployment", "at": f"2026-09-15T12:00:{i:02d}Z",
        "deployment_id": f"hack-{i}", "environment": "production", "outcome": "success",
        "commits": [], "unplanned": False, "caused_by": None
    })

with open("gaming/after.jsonl", "w") as f:
    for e in events: f.write(json.dumps(e) + "\n")

with open("fixtures/events-practice.jsonl") as f:
    ev_b = [json.loads(x) for x in f if x.strip()]

req_b = {"window": {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}, "events": ev_b}
req_a = {"window": {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}, "events": events}

def fetch_metrics(payload):
    req = urllib.request.Request("http://localhost:8080/dora/metrics", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    for _ in range(10):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception:
            time.sleep(1)
    return {}

with open("gaming.json", "w") as f:
    json.dump({"metric": "deployment_frequency_per_day", "rule": "R-11", "before": fetch_metrics(req_b), "after": fetch_metrics(req_a)}, f, indent=2)
