---
lab3_first_draft:
  source: ai
  tool: "Copilot assistant, 11 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]
  verdict: refuted
  evidence: {p99_seconds: 0.2184, bucket: [0.1, 0.25], relative_width: 0.687}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.2184, bucket: [0.04, 0.5], relative_width: 2.106}
---
<!-- ai-generated: 100% - assistant-generated first draft and measured verdict arithmetic -->

# The assistant's first draft, and two verdicts

## Prompt

Suggest Prometheus histogram bucket boundaries in seconds and one Prometheus alert rule for `GET /kb/search`.
The service calls a variable-latency upstream knowledge index; use a conventional general-purpose ladder and an
availability error-budget burn alert. State the bucket values and complete alert expression.

## Answer

Use the common HTTP latency boundaries `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]`
seconds. For an availability objective of 99%, alert when the one-hour ratio of 5xx requests to all
`/kb/search` requests exceeds `14.4 * (1 - 0.99)` for five minutes. This corresponds to a fast error-budget burn
alert; aggregate the numerator and denominator with `sum(rate(...))` and filter by the route template.

## Verdict on the draft ladder

The measured p99 is 0.2184 seconds, in (0.1, 0.25]. That bucket is 0.15 seconds wide, and
0.15 / 0.2184 = 0.687, or 68.7% of p99. It does not resolve the measured slow mode to the required 20%, so the
draft verdict is refuted.

## The draft alert rule

The initial alert suggested only a single one-hour window and a five-minute pending period. The final rules retain
the 14.4 burn rate but pair one-hour and five-minute windows, and add a slower six-hour / 30-minute alert. These
short windows let the alert clear after an incident instead of staying active on a long window alone.

## Verdict on the instructor's flawed ladder

The measured p99 of 0.2184 seconds lies in (0.04, 0.5] in the instructor's ladder. Its width is 0.46 seconds;
0.46 / 0.2184 = 2.106, or 210.6% of p99. This is far above 20%, so the ladder is refuted.
