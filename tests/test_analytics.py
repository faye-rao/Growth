"""M4 — funnel tracking & attribution tests (TDD).

Covers: sequential funnel counts + ordering enforcement + conversion/drop-off
math, the `within_days` window, attribution last_touch vs first_touch + window
+ SENT-only rule, the cross-product funnel differentiator, and divide-by-zero
edge cases.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from growth_common import Channel, DeliveryRecord, DeliveryStatus

from analytics import (
    attribute,
    compute_funnel,
    cross_product_funnel,
)
from analytics.sample_data import (
    NOW,
    build_attribution_data,
    build_cross_product_events,
)


def _ev(cust, name, ts, **props):
    return {"customer_id": cust, "event_name": name, "ts": ts, **props}


T0 = datetime(2026, 6, 1, 9, 0)


# --- funnel: step counts, ordering, conversion/drop-off math ------------------
def test_funnel_step_counts_and_math():
    events = [
        # a: all 3
        _ev("a", "S1", T0), _ev("a", "S2", T0 + timedelta(hours=1)),
        _ev("a", "S3", T0 + timedelta(hours=2)),
        # b: 2 of 3
        _ev("b", "S1", T0), _ev("b", "S2", T0 + timedelta(hours=1)),
        # c: only step 1
        _ev("c", "S1", T0),
        # d: only step 1
        _ev("d", "S1", T0),
    ]
    r = compute_funnel(events, ["S1", "S2", "S3"], now=NOW)
    assert r.step_counts == [4, 2, 1]
    # step-to-step conversion: entry, 2/4, 1/2
    assert r.step_conversion == [1.0, 0.5, 0.5]
    assert r.drop_off == [0, 2, 1]
    assert r.overall_conversion == 0.25
    assert r.entered == 4 and r.completed == 1


def test_funnel_enforces_chronological_order():
    # user did S2 BEFORE S1 -> must NOT count past step 1
    events = [
        _ev("x", "S2", T0),                       # earlier
        _ev("x", "S1", T0 + timedelta(hours=1)),  # later
    ]
    r = compute_funnel(events, ["S1", "S2"], now=NOW)
    # reaches S1 only; the S2 occurrence precedes S1 so it can't advance
    assert r.step_counts == [1, 0]
    assert r.overall_conversion == 0.0


def test_funnel_order_ok_when_later_step_repeats():
    # S2 once before S1 and once after S1 -> the later one should let user advance
    events = [
        _ev("x", "S2", T0),
        _ev("x", "S1", T0 + timedelta(hours=1)),
        _ev("x", "S2", T0 + timedelta(hours=2)),
    ]
    r = compute_funnel(events, ["S1", "S2"], now=NOW)
    assert r.step_counts == [1, 1]


def test_funnel_within_days_filters_late_completions():
    # completes S2 11 days after S1 -> excluded when within_days=7
    events = [
        _ev("p", "S1", T0), _ev("p", "S2", T0 + timedelta(days=11)),
        _ev("q", "S1", T0), _ev("q", "S2", T0 + timedelta(days=2)),
    ]
    r = compute_funnel(events, ["S1", "S2"], now=NOW, within_days=7)
    assert r.step_counts == [2, 1]  # both enter, only q completes in time
    # without the window both complete
    r2 = compute_funnel(events, ["S1", "S2"], now=NOW)
    assert r2.step_counts == [2, 2]


# --- edge cases: no divide-by-zero --------------------------------------------
def test_funnel_empty_events():
    r = compute_funnel([], ["S1", "S2"], now=NOW)
    assert r.step_counts == [0, 0]
    assert r.step_conversion == [1.0, 0.0]
    assert r.drop_off == [0, 0]
    assert r.overall_conversion == 0.0


def test_funnel_requires_steps():
    with pytest.raises(ValueError):
        compute_funnel([], [], now=NOW)


# --- attribution: model differences, window, SENT-only ------------------------
def test_attribution_last_vs_first_touch_differ():
    data = build_attribution_data()
    deliveries, conversions = data["deliveries"], data["conversions"]

    last = attribute(deliveries, conversions, window_hours=24, model="last_touch")
    first = attribute(deliveries, conversions, window_hours=24, model="first_touch")

    # u1 had camp_A (first) then camp_B (last); both within 24h of conversion
    assert last.conversions_per_campaign["camp_B"] == 1
    assert last.conversions_per_campaign["camp_A"] == 0
    assert first.conversions_per_campaign["camp_A"] == 1
    assert first.conversions_per_campaign["camp_B"] == 0


def test_attribution_window_and_sent_only():
    data = build_attribution_data()
    res = attribute(data["deliveries"], data["conversions"],
                    window_hours=24, model="last_touch")
    # u2 only had a FAILED touch -> not attributed; u3 converted outside window.
    # Only u1 is credited.
    assert res.total_conversions == 1
    assert res.unattributed == 2
    # sent denominator counts distinct SENT users per campaign:
    # camp_A: u1,u3 = 2 ; camp_B: u1 = 1  (u2's FAILED touch excluded)
    assert res.sent_per_campaign["camp_A"] == 2
    assert res.sent_per_campaign["camp_B"] == 1
    # conversion rate per campaign = converted / sent
    assert res.conversion_rate_per_campaign["camp_B"] == pytest.approx(1.0)
    assert res.conversion_rate_per_campaign["camp_A"] == pytest.approx(0.0)


def test_attribution_zero_conversions_no_divzero():
    rec = DeliveryRecord("u1", "camp_A", Channel.PUSH, "c1", T0, DeliveryStatus.SENT)
    res = attribute([rec], [], window_hours=24)
    assert res.total_conversions == 0
    assert res.conversion_rate_per_campaign["camp_A"] == 0.0


def test_attribution_no_sent_records_no_divzero():
    rec = DeliveryRecord("u1", "camp_A", Channel.PUSH, "c1", T0, DeliveryStatus.FAILED)
    conv = [_ev("u1", "Conversion", T0 + timedelta(hours=1))]
    res = attribute([rec], conv, window_hours=24)
    # no SENT touch anywhere -> no campaign tracked, conversion unattributed
    assert res.sent_per_campaign == {}
    assert res.unattributed == 1


def test_attribution_rejects_bad_model():
    with pytest.raises(ValueError):
        attribute([], [], window_hours=24, model="middle")


# --- cross-product funnel (the differentiator) --------------------------------
def test_cross_product_funnel_counts():
    events = build_cross_product_events()
    steps = ["Call Active", "Wallet Register", "Remittance First Txn"]
    r = cross_product_funnel(events, steps, now=NOW)
    # u1,u2,u3,u5 enter (Call); u4 did Wallet before Call so still enters via Call.
    # Entry (Call Active): u1,u2,u3,u4,u5 = 5
    # Wallet (in order after Call): u1,u2,u5 = 3 (u4's Wallet precedes its Call)
    # Remittance: u1 and u5 (no window) = 2
    assert r.step_counts == [5, 3, 2]


def test_cross_product_funnel_within_days_drops_late_remittance():
    events = build_cross_product_events()
    steps = ["Call Active", "Wallet Register", "Remittance First Txn"]
    r = cross_product_funnel(events, steps, now=NOW, within_days=7)
    # u5's Remittance is 10 days after its first step -> dropped by the 7d window
    assert r.step_counts == [5, 3, 1]
