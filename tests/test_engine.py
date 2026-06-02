"""M2-A5/A6: engine facade — batch evaluation + audience-size estimation.

Also exercises the three realistic business cohorts used by the demo.
"""
from cohort_engine import CohortEngine, Segment, parse_segment


HIGH_VALUE_NOT_ACTIVATED = {
    "name": "高价值未激活钱包",
    "match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
        {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
    ]},
}

FREQUENT_LOGOUT_ANOMALY = {
    "name": "频繁登出设备异常",
    "match": {"type": "event", "event": "User Logout", "frequency": {"op": "predominantly"},
              "within_days": 3, "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}},
}

KYC_NO_TRANSFER = {
    "name": "KYC未转账",
    "match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"op": "not", "children": [
            {"type": "event", "event": "Transfer", "frequency": {"op": "at_least", "value": 1}, "within_days": 90},
        ]},
    ]},
}


def test_evaluate_returns_ids(engine):
    assert engine.evaluate(HIGH_VALUE_NOT_ACTIVATED) == {"u1", "u4"}
    assert engine.evaluate(FREQUENT_LOGOUT_ANOMALY) == {"u1"}
    assert engine.evaluate(KYC_NO_TRANSFER) == {"u1", "u4"}


def test_estimate_size(engine):
    assert engine.estimate_size(HIGH_VALUE_NOT_ACTIVATED) == 2
    assert engine.estimate_size(KYC_NO_TRANSFER) == 2
    assert engine.estimate_size(FREQUENT_LOGOUT_ANOMALY) == 1


def test_estimate_size_equals_evaluate_len(engine):
    for spec in (HIGH_VALUE_NOT_ACTIVATED, FREQUENT_LOGOUT_ANOMALY, KYC_NO_TRANSFER):
        assert engine.estimate_size(spec) == len(engine.evaluate(spec))


def test_engine_accepts_prebuilt_segment(engine):
    seg = parse_segment(HIGH_VALUE_NOT_ACTIVATED)
    assert isinstance(seg, Segment)
    assert engine.evaluate(seg) == {"u1", "u4"}


def test_compile_sql_roundtrip_smoke(engine):
    s = engine.compile_sql(KYC_NO_TRANSFER)
    assert "u.is_kyc = TRUE" in s
    assert "NOT (" in s
    assert "event_name = 'Transfer'" in s
