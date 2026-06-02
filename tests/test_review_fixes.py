"""Regression tests locking in code-review findings (parity & validation)."""
from datetime import datetime

import pytest

from cohort_engine import CohortEngine
from cohort_engine.parser import RuleParseError, parse_segment
from cohort_engine.sample_data import NOW


def test_not_around_predominantly_sql_is_parenthesized():
    """NOT wrapping a predominantly event must negate the WHOLE predicate (review #1)."""
    eng = CohortEngine(now=NOW)
    spec = {"match": {"op": "not", "children": [
        {"type": "event", "event": "User Logout", "frequency": {"op": "predominantly"},
         "within_days": 3, "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}},
    ]}}
    s = eng.compile_sql(spec)
    # the compound (total>0 AND ratio) is wrapped, then negated as a whole
    assert "NOT (((" in s  # NOT ( ( (total)>0 AND ... ) )


def test_malformed_ts_excluded_within_window():
    """Event without a datetime ts must not count inside a time window (review #3)."""
    dataset = {
        "users": [{"customer_id": "x1"}],
        "events": [
            {"customer_id": "x1", "event_name": "E", "ts": None},          # malformed
            {"customer_id": "x1", "event_name": "E", "ts": "not-a-date"},  # malformed
            {"customer_id": "x1", "event_name": "E", "ts": datetime(2026, 6, 1, 10, 0)},  # valid
        ],
    }
    eng = CohortEngine(dataset, now=NOW)
    # only the 1 valid event falls in the 3-day window
    assert eng.evaluate({"match": {"type": "event", "event": "E",
                                   "frequency": {"op": "exactly", "value": 1}, "within_days": 3}}) == {"x1"}


def test_min_percent_range_validation():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "event", "event": "E",
                                 "frequency": {"op": "min_percent", "value": 150}}})


def test_bool_rejected_as_frequency_value():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "event", "event": "E",
                                 "frequency": {"op": "at_least", "value": True}}})


def test_contains_sql_escapes_wildcards():
    eng = CohortEngine(now=NOW)
    s = eng.compile_sql({"match": {"type": "attribute", "field": "name", "operator": "contains", "value": "50%_off"}})
    assert "ESCAPE '\\'" in s
    assert "50\\%\\_off" in s
