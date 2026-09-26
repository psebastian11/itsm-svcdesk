---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 20% - AI helped draft the edge cases rationale -->
# Edge cases in the practice event log
## E1 - clock skew produces a negative lead time
- What the log contains: A commit timestamped after the deployment.
- What a default definition would have done: Drop it or skew the median negative.
- Why the rule is defensible: We clamp to zero so the delivery event is counted accurately in throughput.
## E2 - a revert of a revert
- What the log contains: A commit reverting another revert.
- What a default definition would have done: Count them as three separate changes.
- Why the rule is defensible: It transitively assigns them to the original change ID, avoiding inflation.
## E3 - a hotfix that never touched main
- What the log contains: A commit deployed from a branch other than main.
- What a default definition would have done: Exclude it entirely.
- Why the rule is defensible: Every commit that reaches production represents real delivery value.
## E4 - a deployment with zero linked commits
- What the log contains: A deployment without commits attached.
- What a default definition would have done: Crash or drop the deployment.
- Why the rule is defensible: Config and infrastructure changes without code commits still carry risk and value.
## E5 - a deployment that failed and never recovered
- What the log contains: A failed deployment with an unresolved incident.
- What a default definition would have done: Invent an end date or drop it.
- Why the rule is defensible: It marks them as open_failures, giving an accurate picture of ongoing instability.
## E6 - overlapping incidents
- What the log contains: Incidents that occur at the same time.
- What a default definition would have done: Merge their durations.
- Why the rule is defensible: Recovery is measured per deployment, giving a true reflection of user impact.
## Gaming demonstration
Improved deployment frequency (R-11) by spamming empty, fake deployments. This artificially boosts the metric without adding business value, actively distracting the team.
