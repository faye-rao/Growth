"""M2 solution C: RoaringBitmap engine — parity with evaluator + bitmap algebra."""
from datetime import timedelta

import pytest

pytest.importorskip("pyroaring")

from cohort_engine import CohortEngine
from cohort_engine.bitmap_engine import BitmapAudienceEngine, BitmapUnsupported
from cohort_engine.sample_data import NOW, build_sample_dataset


def _logout_anomaly(user, events):
    """predominantly logged out with device_height=5 in the last 3 days."""
    lower = NOW - timedelta(days=3)
    logs = [e for e in events if e["event_name"] == "User Logout" and lower <= e["ts"] <= NOW]
    if not logs:
        return False
    dh5 = [e for e in logs if e.get("device_height") == 5]
    return len(dh5) * 2 > len(logs)


TAGS = {"logout_anomaly": _logout_anomaly}


@pytest.fixture
def mem():
    return CohortEngine(build_sample_dataset(), now=NOW)


@pytest.fixture
def bmp():
    return BitmapAudienceEngine(build_sample_dataset(), tag_fns=TAGS, now=NOW)


# --- parity with the in-memory evaluator on attribute cohorts ------------------
ATTR_SPECS = [
    {"match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
        {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
    ]}},
    {"match": {"type": "attribute", "field": "country", "operator": "in", "value": ["AE"]}},
    {"match": {"type": "attribute", "field": "balance", "operator": "between", "value": [1000, 6000]}},
    {"match": {"type": "attribute", "field": "country", "operator": "ne", "value": "AE"}},
    {"match": {"type": "attribute", "field": "country", "operator": "not_in", "value": ["AE"]}},
    {"match": {"type": "attribute", "field": "device_height", "operator": "exists"}},
    {"match": {"type": "attribute", "field": "wallet_activated", "operator": "not_exists"}},
    {"match": {"op": "not", "children": [{"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}]}},
    {
        "match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        "exclude": {"type": "attribute", "field": "country", "operator": "in", "value": ["IN"]},
    },
]


@pytest.mark.parametrize("spec", ATTR_SPECS)
def test_bitmap_matches_evaluator(mem, bmp, spec):
    assert bmp.evaluate(spec) == mem.evaluate(spec)


def test_size_equals_cardinality(bmp, mem):
    spec = ATTR_SPECS[0]
    assert bmp.estimate_size(spec) == len(bmp.evaluate(spec)) == len(mem.evaluate(spec))


# --- event-derived condition via pre-computed boolean tag ----------------------
def test_event_tag_cohort(bmp):
    spec = {"match": {"type": "attribute", "field": "logout_anomaly", "operator": "eq", "value": True}}
    assert bmp.evaluate(spec) == {"u1"}
    assert bmp.estimate_size(spec) == 1


# --- unsupported conditions surface clearly for fallback -----------------------
def test_live_event_condition_unsupported(bmp):
    spec = {"match": {"type": "event", "event": "User Logout", "frequency": {"op": "at_least", "value": 1}}}
    with pytest.raises(BitmapUnsupported):
        bmp.estimate_size(spec)


def test_contains_unsupported(bmp):
    spec = {"match": {"type": "attribute", "field": "country", "operator": "contains", "value": "E"}}
    with pytest.raises(BitmapUnsupported):
        bmp.estimate_size(spec)
