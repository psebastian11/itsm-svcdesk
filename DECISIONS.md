---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: vip
---
<!-- ai-generated: 10% - LLM assistance in phrasing justifications -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 tickets use the 24/7 continuous wall-clock target (15 min ack, 4 h resolve) regardless of business hours.

**Rejected alternative:** Pausing P1 tickets outside Monday-Friday 08:00-16:00 business hours.

**Reason:** Critical incidents impacting the entire organisation require uninterrupted handling; business-hours pausing would delay critical fixes until Monday.

**Service owner:** Incident Management Process Owner and IT Operations Lead.

**Customer outcome:** Immediate triage and around-the-clock remediation for severe outages that completely block business operations.

## C2 - Closed tickets and reopening

**Decision:** Closed tickets are immutable; reopen is permitted exclusively from resolved status within 7 days.

**Rejected alternative:** Allowing reopen directly on closed tickets within a 7-day window.

**Reason:** Closure signifies confirmed customer validation; allowing reopened closed tickets distorts reporting and audit trails. New work must reference the old ticket via related_to.

**Service owner:** Service Desk Team Lead and IT Quality Assurance Manager.

**Customer outcome:** Clear accountability and historical integrity in resolution reports, avoiding stale or ambiguous tickets being reopened unexpectedly.

## C3 - VIP reporters and the priority matrix

**Decision:** Tickets submitted by VIP reporters are elevated to at least P2 whenever the matrix calculates P3 or P4.

**Rejected alternative:** Enforcing strict matrix derivation without any VIP priority promotion.

**Reason:** Operational context requires immediate executive visibility, which standard single-person impact rules would otherwise downgrade to P4.

**Service owner:** IT Director and Customer Success Relationship Manager.

**Customer outcome:** Executive and business-critical stakeholders receive elevated responsiveness and expedited assignment for their operational issues.