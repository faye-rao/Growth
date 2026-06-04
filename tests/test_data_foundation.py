"""Tests for M8 Data Foundation (our part: consumer + glue).

TDD-first. Small deterministic fixtures; fixed reference time so freshness /
timestamp-normalization assertions are stable. Proves the warehouse output is
directly consumable by the M2 ``CohortEngine``.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from cohort_engine import CohortEngine

from data_foundation import (
    DQCReport,
    IdentityResolver,
    IngestResult,
    SuppressionList,
    build_dataset,
    build_event_table,
    build_user_table,
    ingest,
    run_dqc,
    to_dubai,
)

# Fixed reference "now" in Dubai local time (UTC+4), matching the M2 sample data.
NOW = datetime(2026, 6, 2, 12, 0, 0)


# --------------------------------------------------------------------------- #
# ingestion
# --------------------------------------------------------------------------- #
SCHEMA = {
    "App Opened": {"customer_id": str},
    "Transfer": {"customer_id": str, "amount": (int, float)},
}


def _raw(event_id, name, cid, ts_utc, **props):
    return {"event_id": event_id, "event_name": name, "customer_id": cid,
            "ts_utc": ts_utc, **props}


def test_ingest_normalizes_ts_to_dubai_plus_4h():
    raw = [_raw("e1", "App Opened", "u1", datetime(2026, 6, 2, 5, 0, 0))]
    result = ingest(raw, SCHEMA, now=NOW)
    assert isinstance(result, IngestResult)
    assert len(result.clean) == 1
    # 05:00 UTC -> 09:00 Asia/Dubai
    assert result.clean[0]["ts"] == datetime(2026, 6, 2, 9, 0, 0)
    # raw ts_utc preserved for audit
    assert result.clean[0]["ts_utc"] == datetime(2026, 6, 2, 5, 0, 0)


def test_to_dubai_is_fixed_plus_4_offset():
    assert to_dubai(datetime(2026, 1, 1, 0, 0, 0)) == datetime(2026, 1, 1, 4, 0, 0)
    # no DST: a summer date uses the same +4 offset
    assert to_dubai(datetime(2026, 7, 1, 22, 0, 0)) == datetime(2026, 7, 2, 2, 0, 0)


def test_ingest_quarantines_invalid_event_not_dropped():
    raw = [
        _raw("e1", "App Opened", "u1", datetime(2026, 6, 2, 5, 0, 0)),
        _raw("e2", "Transfer", "u2", datetime(2026, 6, 2, 6, 0, 0)),  # missing amount
        _raw("e3", "Transfer", "u3", datetime(2026, 6, 2, 6, 0, 0), amount="oops"),  # bad type
        _raw("e4", "Unknown Event", "u4", datetime(2026, 6, 2, 6, 0, 0)),  # unknown schema
    ]
    result = ingest(raw, SCHEMA, now=NOW)
    assert len(result.clean) == 1
    assert {q["event_id"] for q in result.quarantined} == {"e2", "e3", "e4"}
    # quarantined records carry a reason, are not silently dropped
    assert all("reason" in q for q in result.quarantined)


def test_ingest_dedups_by_event_id():
    ts = datetime(2026, 6, 2, 5, 0, 0)
    raw = [
        _raw("e1", "App Opened", "u1", ts),
        _raw("e1", "App Opened", "u1", ts),  # exact duplicate event_id -> collapsed
        _raw("e2", "App Opened", "u1", ts),  # different event_id -> kept (distinct event)
    ]
    result = ingest(raw, SCHEMA, now=NOW)
    assert len(result.clean) == 2
    assert result.deduped == 1


def test_ingest_keeps_distinct_events_sharing_natural_key():
    # two genuinely-distinct Transfers in the same second (different amounts) must
    # both survive — they carry different event_ids (review finding #1 regression).
    ts = datetime(2026, 6, 2, 5, 0, 0)
    raw = [
        _raw("t1", "Transfer", "u1", ts, amount=100),
        _raw("t2", "Transfer", "u1", ts, amount=250),
    ]
    result = ingest(raw, SCHEMA, now=NOW)
    assert len(result.clean) == 2
    assert result.deduped == 0
    assert {e["amount"] for e in result.clean} == {100, 250}


def test_ingest_dedups_by_natural_key_when_no_event_id():
    ts = datetime(2026, 6, 2, 5, 0, 0)
    raw = [
        {"event_name": "App Opened", "customer_id": "u1", "ts_utc": ts},
        {"event_name": "App Opened", "customer_id": "u1", "ts_utc": ts},  # no id -> natural-key dup
    ]
    result = ingest(raw, SCHEMA, now=NOW)
    assert len(result.clean) == 1
    assert result.deduped == 1


# --------------------------------------------------------------------------- #
# identity resolution
# --------------------------------------------------------------------------- #
def test_resolve_uses_priority_customer_id_over_phone_over_device():
    r = IdentityResolver()
    r.add_mapping("device:d1", "u1")  # device_id resolves only via the data-team mapping
    # customer_id wins over phone/device
    assert r.resolve({"customer_id": "u9", "phone": "+97150", "device_id": "d1"}) == "u9"
    # phone (a primary key) wins over device; unmapped phone resolves to itself
    assert r.resolve({"phone": "+97150", "device_id": "d1"}) == "+97150"
    # device alone resolves only through the mapping (not a primary key)
    assert r.resolve({"device_id": "d1"}) == "u1"


def test_phone_and_device_of_same_user_resolve_to_one_customer_id():
    r = IdentityResolver()
    # data-team mapping: alt identifiers -> canonical customer_id
    r.add_mapping("phone:+97150", "u1")
    r.add_mapping("device:d1", "u1")
    assert r.resolve({"phone": "+97150"}) == "u1"
    assert r.resolve({"device_id": "d1"}) == "u1"
    assert r.resolve({"phone": "+97150"}) == r.resolve({"device_id": "d1"})


def test_merge_unions_two_ids():
    r = IdentityResolver()
    r.add_mapping("phone:+97150", "uA")
    r.add_mapping("device:d9", "uB")
    r.merge("uA", "uB")
    # after merge both alt identifiers resolve to the same canonical id
    assert r.resolve({"phone": "+97150"}) == r.resolve({"device_id": "d9"})


def test_coverage_reports_pct_resolvable():
    r = IdentityResolver()
    r.add_mapping("phone:+97150", "u1")
    inputs = [
        {"customer_id": "u2"},      # resolvable (has customer_id)
        {"phone": "+97150"},        # resolvable (mapped -> u1)
        {"device_id": "d-unknown"}, # unresolvable (device alone, unmapped)
        {},                         # unresolvable (nothing)
    ]
    assert r.coverage(inputs) == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# warehouse — compatibility with M2 CohortEngine
# --------------------------------------------------------------------------- #
def test_build_user_table_joins_labels():
    users = [{"customer_id": "u1"}, {"customer_id": "u2"}]
    labels = {"u1": {"is_kyc": True, "dormant": False}}
    table = build_user_table(users, labels)
    u1 = next(u for u in table if u["customer_id"] == "u1")
    assert u1["is_kyc"] is True and u1["dormant"] is False
    # missing label set leaves the user intact (no crash)
    u2 = next(u for u in table if u["customer_id"] == "u2")
    assert u2["customer_id"] == "u2"


def test_build_dataset_runs_through_cohort_engine():
    users = [
        {"customer_id": "u1", "balance": 5000},
        {"customer_id": "u2", "balance": 100},
    ]
    labels = {"u1": {"is_kyc": True}, "u2": {"is_kyc": False}}
    clean_events = [
        {"event_id": "e1", "customer_id": "u1", "event_name": "App Opened",
         "ts": datetime(2026, 6, 2, 9, 0, 0)},
    ]
    dataset = build_dataset(users, labels, clean_events)
    assert set(dataset.keys()) == {"users", "events"}

    engine = CohortEngine(dataset, now=NOW)
    rule = {"match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
    ]}}
    assert engine.evaluate(rule) == {"u1"}

    # event condition also works through the rebuilt event table
    rule_ev = {"match": {"type": "event", "event": "App Opened",
                         "frequency": {"op": "at_least", "value": 1}}}
    assert engine.evaluate(rule_ev) == {"u1"}


# --------------------------------------------------------------------------- #
# data-quality checks
# --------------------------------------------------------------------------- #
def _clean_dataset():
    users = [{"customer_id": "u1", "is_kyc": True},
             {"customer_id": "u2", "is_kyc": False}]
    events = [
        {"event_id": "e1", "customer_id": "u1", "event_name": "App Opened",
         "ts": datetime(2026, 6, 2, 11, 30, 0)},
        {"event_id": "e2", "customer_id": "u2", "event_name": "App Opened",
         "ts": datetime(2026, 6, 2, 11, 0, 0)},
    ]
    return {"users": users, "events": events}


def test_dqc_clean_dataset_passes():
    report = run_dqc(_clean_dataset(), now=NOW, thresholds={
        "null_rate": 0.0, "dup_rate": 0.0, "max_latency_hours": 24})
    assert isinstance(report, DQCReport)
    assert report.ok
    assert report.alerts == []


def test_dqc_flags_nulls_dupes_and_staleness():
    dataset = {
        "users": [{"customer_id": "u1", "is_kyc": True},
                  {"customer_id": None, "is_kyc": False}],  # null key -> null_rate
        "events": [
            {"event_id": "e1", "customer_id": "u1", "event_name": "App Opened",
             "ts": datetime(2026, 5, 1, 0, 0, 0)},  # stale -> latency
            {"event_id": "e1", "customer_id": "u1", "event_name": "App Opened",
             "ts": datetime(2026, 5, 1, 0, 0, 0)},  # dup idempotency key
        ],
    }
    report = run_dqc(dataset, now=NOW, thresholds={
        "null_rate": 0.0, "dup_rate": 0.0, "max_latency_hours": 24})
    assert not report.ok
    failed = {a["check"] for a in report.alerts}
    assert {"null_rate", "dup_rate", "freshness"} <= failed


# --------------------------------------------------------------------------- #
# suppression (near-real-time "already converted -> don't message again")
# --------------------------------------------------------------------------- #
def test_suppression_removes_converted_keeps_rest():
    conversions = [
        {"customer_id": "u1", "event_name": "Transfer"},
        {"customer_id": "u3", "event_name": "Transfer"},
    ]
    sup = SuppressionList.from_conversions(conversions)
    assert sup.contains("u1")
    kept, suppressed = sup.filter(["u1", "u2", "u3", "u4"])
    assert kept == ["u2", "u4"]
    assert suppressed == ["u1", "u3"]
