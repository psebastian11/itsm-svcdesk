---
lab4_comms:
  awareness: 2026-10-12T06:40:09Z
  detection: 2026-10-12T06:39:19Z
  classification: 2026-10-12T06:50:00Z
  nis2:
    early_warning_due: 2026-10-13T06:40:09Z
    notification_due: 2026-10-15T06:40:09Z
    notification_sent: 2026-10-12T08:00:00Z
    final_report_due: 2026-11-12T08:00:00Z
  ksc:
    early_warning_due: 2026-10-13T06:39:19Z
    notification_due: 2026-10-15T06:39:19Z
    notification_sent: 2026-10-12T08:00:00Z
    final_report_due: 2026-11-12T08:00:00Z
  dora:
    initial_due: 2026-10-12T10:50:00Z
    initial_sent: 2026-10-12T07:30:00Z
    intermediate_due: 2026-10-15T07:30:00Z
    intermediate_sent: 2026-10-15T07:30:00Z
    final_due: 2026-11-15T07:30:00Z
  log:
    - {at: 2026-10-12T06:40:09Z, to: incident management, what: "On-call acknowledged the P1 page and treated the checkout failures as a significant incident."}
    - {at: 2026-10-12T07:30:00Z, to: DORA supervisory authority, what: "Send the initial major ICT incident notification before the four-hour classification deadline."}
    - {at: 2026-10-12T08:00:00Z, to: NIS2 and KSC authorities, what: "Send the initial incident notifications while preserving time for the required final reports."}
---
<!-- ai-generated: 80% - calculated the NIS2, KSC, and DORA deadlines from the recorded incident instants -->

# Communications log: the regulators' clocks

## The three instants you defend

Awareness is 06:40:09Z, when the on-call acknowledged the P1 ticket and had enough incident context to judge the checkout failures significant. KSC detection is 06:39:19Z, the recomputed start of ShopCheckoutErrors. DORA classification is 06:50:00Z, after the incident was assessed as a major ICT-related incident; the supplied snapshot and ticket do not establish a more precise classification time.

## The log

The proposed DORA initial report is sent at 07:30Z, before its 10:50Z deadline. The NIS2 and KSC notifications are sent at 08:00Z, leaving substantial time before both 72-hour deadlines. The DORA intermediate report is scheduled exactly 72 hours after the initial submission. The final report dates follow the calendar-month rule from their respective submission instants.
