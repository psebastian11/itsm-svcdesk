---
lab4_postmortem:
  ticket: "50ceffde-fa49-40b3-b4ca-957734d74bf7"
  detecting_alert: ShopCheckoutErrors
  onset: 2026-10-12T06:36:23Z
  detection: 2026-10-12T06:39:19Z
  acknowledgement: 2026-10-12T06:40:09Z
  recovery: 2026-10-12T06:44:19Z
  mttd_seconds: 176
  mtta_seconds: 50
  mttr_seconds: 476
  identified_flags: [paymentFailure, loadGeneratorFloodHomepage]
---
<!-- ai-generated: 80% - drafted from the assigned recording, its snapshot, ticket, and scored transcript -->

# Postmortem: Checkout failures during the recorded shop incident

## Date

The recorded incident occurred on 12 October 2026; this postmortem was prepared on 25 October 2026.

## Authors

Prepared by psebastian11 in the role of the on-call incident responder for the recorded exercise.

## Status

The recorded incident is recovered; the evidence and AI scorecard are documented, with follow-up actions proposed.

## Summary

Checkout orders failed during a recorded shop incident, detected by ShopCheckoutErrors at 06:39:19 UTC. The recomputed alert recovery was 06:44:19 UTC, 7 minutes 56 seconds after the incident onset.

## Impact

At 06:42:00 UTC, payment charge errors and checkout PlaceOrder server errors each measured 0.0321 spans per second using five-minute `rate(traces_span_metrics_calls_total{...}[5m])` queries. Frontend server traffic was 63.41 spans per second versus 3.81 at the 06:31:23 UTC healthy-baseline instant, consistent with a homepage load surge. These measurements describe span rates, not unique affected customers.

## Root Causes

Payment's internal charge span and checkout's downstream payment and PlaceOrder spans reported errors. The recorded metrics support a payment failure and a substantial frontend request surge; they do not expose the sealed third fault or prove a causal chain from correlation alone.

## Trigger

The snapshot marks the seeded fault active at 06:36:23 UTC. Checkout failures were detected 176 seconds later; the sealed fault details are intentionally unavailable on the recorded path.

## Resolution

The recorded run recovered at 06:44:19 UTC when the detecting alert's firing run ended. The supplied snapshot and ticket do not record per-flag switch-off timestamps or order, so no unsupported rollback sequence is asserted here.

## Detection

ShopCheckoutErrors detected the incident at 06:39:19 UTC from checkout symptoms, producing an MTTD of 176 seconds. Without this page, the on-call would have needed to notice the customer-facing order errors in service telemetry.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a dashboard panel for checkout PlaceOrder error rate and payment Charge errors with a shared incident time range. | prevent | Shop SRE | ITSM-101 |
| Add a load-surge guardrail and a runbook step to compare frontend request rate with the healthy baseline. | mitigate | On-call lead | ITSM-102 |

## Lessons Learned

### What went well

The incident has a P1 ticket, a recorded acknowledgement, and a recomputable detection and recovery timeline.

### What went wrong

The recorded AI investigator used timestamps outside the incident window for follow-up queries, limiting its ability to validate the apparent cause.

### Where we got lucky

The recorded run recovered, and checkout and payment errors were visible in telemetry without needing access to customer data.

## Timeline

- 06:36:23 UTC — seeded fault onset in the snapshot; the service symptoms begin.
- 06:39:19 UTC — ShopCheckoutErrors fires and detects the incident (H1/H2 payment-charge predictions and H4 checkout PlaceOrder prediction are scored against five-minute PromQL windows at 06:42:00 UTC).
- 06:40:09 UTC — the P1 ticket is acknowledged, 50 seconds after detection.
- 06:44:19 UTC — the detecting alert resolves; this is the recomputed recovery, 476 seconds after onset.
- After recovery — H3's payment/checkout correlation prediction is scored as partial: both signals are present, but correlation alone does not establish causation.

## Supporting information

The assigned `lab4-rec-4` snapshot and unchanged ticket are the source of the four instants. `itsmlab incident 4` recomputed ShopCheckoutErrors, onset 06:36:23Z, detection 06:39:19Z, acknowledgement 06:40:09Z, recovery 06:44:19Z, MTTD 176 s, MTTA 50 s and MTTR 476 s. The four transcript claims and their filtering PromQL comparisons are recorded in `ai-rca-eval.json`; the comparison instants are 06:42:00Z and the healthy baseline 06:31:23Z.

## Problem record

- Incident record: P1 ticket 50ceffde-fa49-40b3-b4ca-957734d74bf7 documents the checkout incident and acknowledgement.
- Root cause: Payment charge failures coincide with checkout failures and an unusually high frontend request rate.
- Known error: The recorded evidence does not reveal the sealed third flag or prove which individual change initiated the failure.
- Workaround: The recorded incident recovered; use the service and load metrics to guide rollback when reproducing it.
