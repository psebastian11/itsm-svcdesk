# ai-generated: 90% - wrote Semgrep test cases for the svcdesk-specific guardrails
from datetime import datetime, timezone


def direct_state_change(db, ticket_id, new_state):
    # ruleid: svcdesk-ticket-state-direct-write
    db[ticket_id]["state"] = new_state


def checked_state_change(db, ticket_id, new_state):
    # ok: svcdesk-ticket-state-direct-write
    transition_ticket(db, ticket_id, new_state)


def get_now(value):
    # ruleid: svcdesk-test-clock-normalizes-utc
    return datetime.fromisoformat(value)


def get_now():
    # ok: svcdesk-test-clock-normalizes-utc
    return datetime.now(timezone.utc)
