<!-- ai-generated: 0% - written by the course team -->
# svcdesk - ITSM 2026/27 course repository

This repository was created from the course template. It holds your `svcdesk` service for the whole semester:
built in Lab 1, extended in the later labs. Keep it public, and keep personal data out of it.

## The one command

    ./itsmlab.sh verify 1            # Linux, macOS
    .\itsmlab.ps1 verify 1           # Windows PowerShell (once before: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)

It runs the published Tier A checker (a container) against this directory: builds and starts your service with
`docker compose`, runs the published checks, prints a table, and exits 0 when every Core spec passes. Add
`--json report.json` to keep the machine-readable report. Tier A runs are unlimited and never count as attempts.

Before the first run: fill in `repository:` in `itsmlab.yaml`, copy `Dockerfile.example` to `Dockerfile` (or
write your own), and read the course package (`README.md`, `PREWORK.md`, `lab1/`), published on Moodle.

## Layout

| path | what it is |
|---|---|
| `docker-compose.yml` | the compose contract: service `svcdesk` on 8080, `SVCDESK_TEST_CLOCK`, a named volume; `tests` profile commented out |
| `Dockerfile.example` | a Python 3.13 image skeleton; copy to `Dockerfile` or replace for your language |
| `DECISIONS.md` | your reasoning artifact: front matter with the three decisions, three sections, five labels each |
| `itsmlab.yaml` | lab number, baselines, your repository, the submissions repository, the checker image |
| `itsmlab.sh`, `itsmlab.ps1` | wrappers that run the checker container |
| `specs/` | your specifications, published and receipted before any code |
| `src/` | your implementation |
| `.github/workflows/tier-a.yml` | runs the checker on every push and publishes `report.json` as an artifact with a step summary |

## Lab 3 observability

`GET /kb/search?q=...` forwards searches to `kb-index`; `/metrics` exposes the request-duration histogram used by
the Prometheus alert rules and Grafana dashboard. Start the dependency with the service, and start the optional
monitoring stack with `docker compose --profile observability up -d`.

## Lab 4 incident response

The shop symptom alerts are in `prometheus/demo-alerts.yml`; `alertmanager/` contains the pager/chat routing
configuration and executable routing/inhibition cases. The assigned live or recorded incident evidence belongs in
`incident/`, with its recomputed timestamps documented in `postmortem.md` and its investigated hypotheses in
`ai-rca-eval.json`. Keep snapshot and ticket artifacts unchanged from the course source.
| `.gitignore` | keeps `report.json`, virtual environments and local data out of git |
| `.gitattributes` | LF line endings on every system, so the checker's git sees a clean tree on Windows too; keep it |

## Every push runs the checker

The workflow `tier-a` runs on every push and on demand (Actions tab, "Run workflow"). It needs no secrets. The
job is red when a Core spec fails; the step summary shows which checks, and `report.json` is attached as an
artifact.
