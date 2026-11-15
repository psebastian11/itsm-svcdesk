# ai-generated: 90% - wrote behavioral tests from the Lab 5 slaclock docstrings
from datetime import datetime

import pytest

from slaclock import (
    add_business_minutes,
    business_minutes_between,
    escalation_tier,
    is_business_time,
    parse_duration,
    priority_of,
    sla_state,
    targets,
)


@pytest.mark.parametrize(
    ("impact", "urgency", "priority"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (1, 3, "P3"),
        (2, 2, "P3"),
        (3, 1, "P3"),
        (2, 3, "P4"),
        (3, 2, "P4"),
        (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, priority):
    assert priority_of(impact, urgency) == priority


def test_vip_promotes_only_lower_priorities():
    assert priority_of(1, 1, vip=True) == "P1"
    assert priority_of(1, 2, vip=True) == "P2"
    assert priority_of(1, 3, vip=True) == "P2"
    assert priority_of(3, 3, vip=True) == "P2"


@pytest.mark.parametrize("value", [0, 4, 2.0, True, "1"])
def test_priority_rejects_non_integer_or_out_of_range_values(value):
    with pytest.raises(ValueError):
        priority_of(value, 1)
    with pytest.raises(ValueError):
        priority_of(1, value)


@pytest.mark.parametrize(
    ("priority", "expected"),
    [
        ("P1", (15, 240)),
        ("P2", (60, 480)),
        ("P3", (240, 1440)),
        ("P4", (480, 4320)),
    ],
)
def test_priority_targets(priority, expected):
    assert targets(priority) == expected


@pytest.mark.parametrize("priority", ["p1", " P1", "P5", ""])
def test_targets_requires_exact_priority(priority):
    with pytest.raises(ValueError):
        targets(priority)


def test_sla_state_boundaries_are_inclusive_at_warning_and_target():
    assert sla_state(0, 15) == "ok"
    assert sla_state(11, 15) == "ok"
    assert sla_state(12, 15) == "warning"
    assert sla_state(15, 15) == "warning"
    assert sla_state(16, 15) == "breached"
    assert sla_state(3, 4) == "warning"


@pytest.mark.parametrize(("elapsed", "target"), [(-1, 15), (0, 0), (1, -1)])
def test_sla_state_rejects_invalid_durations(elapsed, target):
    with pytest.raises(ValueError):
        sla_state(elapsed, target)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 11, 16, 8, 0), True),
        (datetime(2026, 11, 16, 15, 59), True),
        (datetime(2026, 11, 16, 7, 59), False),
        (datetime(2026, 11, 16, 16, 0), False),
        (datetime(2026, 11, 21, 10, 0), False),
    ],
)
def test_business_time_window(moment, expected):
    assert is_business_time(moment) is expected


def test_add_business_minutes_clips_to_business_days_and_preserves_closing_boundary():
    monday = datetime(2026, 11, 16, 8, 0)
    assert add_business_minutes(monday, 0) == monday
    assert add_business_minutes(datetime(2026, 11, 16, 7, 0), 0) == monday
    assert add_business_minutes(datetime(2026, 11, 16, 16, 0), 0) == datetime(2026, 11, 17, 8, 0)
    assert add_business_minutes(datetime(2026, 11, 20, 15, 0), 60) == datetime(2026, 11, 20, 16, 0)
    assert add_business_minutes(datetime(2026, 11, 20, 15, 0), 61) == datetime(2026, 11, 23, 8, 1)
    assert add_business_minutes(datetime(2026, 11, 21, 10, 0), 60) == datetime(2026, 11, 23, 9, 0)


def test_add_business_minutes_discards_seconds_and_handles_multiple_days():
    start = datetime(2026, 11, 16, 15, 30, 45, 500)
    assert add_business_minutes(start, 90) == datetime(2026, 11, 17, 9, 0)
    assert add_business_minutes(datetime(2026, 11, 16, 8, 0), 960) == datetime(2026, 11, 17, 16, 0)


@pytest.mark.parametrize("minutes", [-1, 366 * 24 * 60])
def test_add_business_minutes_rejects_invalid_or_too_long_targets(minutes):
    with pytest.raises(ValueError):
        add_business_minutes(datetime(2026, 11, 16, 8, 0), minutes)


def test_business_minutes_between_uses_half_open_business_windows():
    monday = datetime(2026, 11, 16, 8, 0)
    assert business_minutes_between(monday, monday) == 0
    assert business_minutes_between(datetime(2026, 11, 16, 7, 0), datetime(2026, 11, 16, 9, 0)) == 60
    assert business_minutes_between(datetime(2026, 11, 16, 15, 0), datetime(2026, 11, 17, 9, 0)) == 120
    assert business_minutes_between(datetime(2026, 11, 20, 15, 0), datetime(2026, 11, 23, 9, 0)) == 120


@pytest.mark.parametrize(
    ("start", "minutes"),
    [
        (datetime(2026, 11, 16, 8, 0), 0),
        (datetime(2026, 11, 16, 15, 0), 60),
        (datetime(2026, 11, 20, 15, 0), 61),
        (datetime(2026, 11, 21, 10, 0), 480),
    ],
)
def test_business_clock_round_trip(start, minutes):
    due = add_business_minutes(start, minutes)
    assert business_minutes_between(start, due) == minutes


def test_business_minutes_between_rejects_reversed_and_excessive_windows():
    with pytest.raises(ValueError):
        business_minutes_between(datetime(2026, 11, 17), datetime(2026, 11, 16))
    with pytest.raises(ValueError):
        business_minutes_between(datetime(2025, 1, 1), datetime(2026, 1, 3))


def test_escalation_tier_priority_breach_and_reopens():
    assert escalation_tier("P1", False, 0) == 1
    assert escalation_tier("P2", False, 0) == 1
    assert escalation_tier("P3", False, 0) == 0
    assert escalation_tier("P1", True, 0) == 3
    assert escalation_tier("P2", True, 0) == 2
    assert escalation_tier("P4", False, 2) == 1
    assert escalation_tier("P2", True, 2) == 3


@pytest.mark.parametrize(("priority", "reopens"), [("P5", 0), ("P1", -1)])
def test_escalation_rejects_unknown_priority_or_negative_reopens(priority, reopens):
    with pytest.raises(ValueError):
        escalation_tier(priority, False, reopens)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", 90),
        ("4h", 240),
        ("1h30m", 90),
        ("2d", 2880),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("1h59m", 119),
        ("60m", 60),
        ("0h60m", 60),
        (" 2d ", 2880),
    ],
)
def test_parse_duration_accepts_documented_forms(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "0m", "1.5h", "30m1h", "-5m", "1 h", "1h60m", "1d60m", "1h1h", "1d1d", "1H"],
)
def test_parse_duration_rejects_invalid_forms(text):
    with pytest.raises(ValueError):
        parse_duration(text)
