"""M2 solution B: compile-to-SQL. Asserts key fragments of generated SQL."""
from cohort_engine import CohortEngine
from cohort_engine.sample_data import NOW


def sql(match, exclude=None, count=False):
    eng = CohortEngine(now=NOW)
    spec = {"match": match}
    if exclude is not None:
        spec["exclude"] = exclude
    return eng.compile_count_sql(spec) if count else eng.compile_sql(spec)


def test_attribute_eq_bool():
    s = sql({"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True})
    assert s.startswith("SELECT DISTINCT u.customer_id FROM users u WHERE")
    assert "u.is_kyc = TRUE" in s


def test_in_and_between():
    s = sql({"op": "and", "children": [
        {"type": "attribute", "field": "country", "operator": "in", "value": ["AE", "PH"]},
        {"type": "attribute", "field": "balance", "operator": "between", "value": [1000, 6000]},
    ]})
    assert "u.country IN ('AE', 'PH')" in s
    assert "u.balance BETWEEN 1000 AND 6000" in s


def test_string_literal_is_escaped():
    s = sql({"type": "attribute", "field": "country", "operator": "eq", "value": "O'Brien"})
    assert "u.country = 'O''Brien'" in s


def test_event_at_least_subquery():
    s = sql({"type": "event", "event": "Push ID Register Android",
             "frequency": {"op": "at_least", "value": 1}, "within_days": 3})
    assert "SELECT COUNT(*) FROM events e" in s
    assert "e.event_name = 'Push ID Register Android'" in s
    assert "INTERVAL '3' DAY" in s
    assert ">= 1" in s


def test_event_predominantly_uses_ratio():
    s = sql({"type": "event", "event": "User Logout", "frequency": {"op": "predominantly"},
             "within_days": 3, "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}})
    assert "* 2 >" in s            # matching*2 > total
    assert "e.device_height = 5" in s


def test_time_dimension_compiles_to_extract():
    s = sql({"type": "event", "event": "User Logout", "frequency": {"op": "at_least", "value": 1},
             "within_days": 3, "where": {"type": "attribute", "field": "hour_of_day", "operator": "between", "value": [0, 5]}})
    assert "EXTRACT(HOUR FROM e.ts)" in s
    assert "BETWEEN 0 AND 5" in s


def test_not_group_and_exclude():
    s = sql(
        match={"op": "not", "children": [{"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}]},
        exclude={"type": "attribute", "field": "country", "operator": "in", "value": ["IN"]},
    )
    assert "NOT (u.is_kyc = TRUE)" in s
    assert "AND NOT (u.country IN ('IN'))" in s


def test_count_query():
    s = sql({"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}, count=True)
    assert s.startswith("SELECT COUNT(DISTINCT u.customer_id) FROM users u WHERE")
