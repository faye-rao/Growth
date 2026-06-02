"""M2-A1~A4: evaluation semantics over the deterministic sample dataset."""
import pytest

from cohort_engine import CohortEngine


def ev(engine, match, exclude=None):
    spec = {"match": match}
    if exclude is not None:
        spec["exclude"] = exclude
    return engine.evaluate(spec)


# --- M2-A3 attribute operators -------------------------------------------------
@pytest.mark.parametrize("match, expected", [
    ({"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}, {"u1", "u2", "u4", "u5"}),
    ({"type": "attribute", "field": "country", "operator": "ne", "value": "AE"}, {"u2", "u3"}),
    ({"type": "attribute", "field": "balance", "operator": "gt", "value": 1000}, {"u1", "u4", "u5"}),
    ({"type": "attribute", "field": "balance", "operator": "gte", "value": 5000}, {"u1", "u5"}),
    ({"type": "attribute", "field": "balance", "operator": "lt", "value": 1000}, {"u2", "u3"}),
    ({"type": "attribute", "field": "balance", "operator": "lte", "value": 200}, {"u2", "u3"}),
    ({"type": "attribute", "field": "country", "operator": "in", "value": ["AE", "PH"]}, {"u1", "u3", "u4", "u5"}),
    ({"type": "attribute", "field": "country", "operator": "not_in", "value": ["AE"]}, {"u2", "u3"}),
    ({"type": "attribute", "field": "balance", "operator": "between", "value": [1000, 6000]}, {"u1", "u4"}),
    ({"type": "attribute", "field": "device_height", "operator": "exists"}, {"u1", "u2", "u3", "u4", "u5"}),
    ({"type": "attribute", "field": "country", "operator": "contains", "value": "E"}, {"u1", "u4", "u5"}),
])
def test_attribute_operators(engine, match, expected):
    assert ev(engine, match) == expected


def test_not_exists_on_universal_field_is_empty(engine):
    assert ev(engine, {"type": "attribute", "field": "wallet_activated", "operator": "not_exists"}) == set()


# --- M2-A1 nested AND/OR/NOT ---------------------------------------------------
def test_nested_and_or_not(engine):
    # KYC AND (balance>=1000 OR country in [PH])
    match = {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"op": "or", "children": [
            {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
            {"type": "attribute", "field": "country", "operator": "in", "value": ["PH"]},
        ]},
    ]}
    assert ev(engine, match) == {"u1", "u4", "u5"}


def test_not_group_negates(engine):
    # NOT(is_kyc) -> only u3
    match = {"op": "not", "children": [{"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}]}
    assert ev(engine, match) == {"u3"}


# --- M2-A4 exclude -------------------------------------------------------------
def test_exclude_users(engine):
    match = {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}      # u1,u2,u4,u5
    exclude = {"type": "attribute", "field": "country", "operator": "in", "value": ["IN"]}  # removes u2
    assert ev(engine, match, exclude) == {"u1", "u4", "u5"}


# --- M2-A3 frequency operators -------------------------------------------------
def _logout(freq, within=3, where=None):
    cond = {"type": "event", "event": "User Logout", "frequency": freq, "within_days": within}
    if where is not None:
        cond["where"] = where
    return cond


DH5 = {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}


def test_frequency_at_least_with_where(engine):
    assert ev(engine, _logout({"op": "at_least", "value": 2}, where=DH5)) == {"u1"}
    assert ev(engine, _logout({"op": "at_least", "value": 3}, where=DH5)) == set()


def test_frequency_exactly_and_at_most(engine):
    assert ev(engine, _logout({"op": "exactly", "value": 2}, where=DH5)) == {"u1"}
    # at_most 0 with where dh5: u1 has 2 -> excluded; users with no logout match (0<=0)
    assert "u1" not in ev(engine, _logout({"op": "at_most", "value": 0}, where=DH5))


def test_frequency_predominantly(engine):
    # u1: 2 of 3 logouts have dh=5 -> predominantly True; u3: 0 of 1 -> False
    assert ev(engine, _logout({"op": "predominantly"}, where=DH5)) == {"u1"}


def test_frequency_min_percent(engine):
    assert ev(engine, _logout({"op": "min_percent", "value": 50}, where=DH5)) == {"u1"}   # 2/3=66%
    assert ev(engine, _logout({"op": "min_percent", "value": 70}, where=DH5)) == set()    # 66% < 70%


# --- M2-A2 time window ---------------------------------------------------------
def test_time_window_filters_old_events(engine):
    # Without where: u1 has 3 logouts within 3 days (old 2026-04-01 excluded)
    assert ev(engine, _logout({"op": "exactly", "value": 3})) == {"u1"}
    # With a 90-day window the old event is included -> 4
    assert ev(engine, _logout({"op": "exactly", "value": 4}, within=90)) == {"u1"}


def test_push_register_within_window(engine):
    # u2 registered within 3 days; u4's registration is old (2026-05-20) -> excluded
    cond = {"type": "event", "event": "Push ID Register Android", "frequency": {"op": "at_least", "value": 1}, "within_days": 3}
    assert ev(engine, cond) == {"u2"}


# --- event time-dimension where (hour_of_day / month_of_year) ------------------
def test_event_time_dimension_where(engine):
    # User Logout where hour_of_day between 0..5 -> only u1's 03:00 event qualifies
    cond = _logout({"op": "at_least", "value": 1}, where={
        "type": "attribute", "field": "hour_of_day", "operator": "between", "value": [0, 5]})
    assert ev(engine, cond) == {"u1"}

    # month_of_year == 5 within 30 days -> u1's 2026-05-31 logout qualifies
    cond_m = _logout({"op": "at_least", "value": 1}, within=30, where={
        "type": "attribute", "field": "month_of_year", "operator": "eq", "value": 5})
    assert ev(engine, cond_m) == {"u1"}
