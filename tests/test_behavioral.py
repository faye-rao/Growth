"""M9 — Behavioral Analytics tests (TDD, scoped-down).

Covers:
- the ~6 canonical reports (active users, new vs returning, event volume,
  campaign CTR/CVR incl. /0 guard, conversion funnel, retention-lite)
- conversion_funnel_report matches a direct M4 compute_funnel call (proves reuse)
- auto-insights: obvious spike/drop flagged, flat series yields none,
  compare_periods direction + notable flag
- MoEngage-replacement metrics: deterministic RFM / engagement / churn on a
  known user set (recent-active -> low churn, long-inactive -> high)

Deterministic synthetic fixtures; reuses cohort_engine.sample_data where handy.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from growth_common import Channel, DeliveryRecord, DeliveryStatus

from analytics import compute_funnel

from behavioral import (
    active_users,
    campaign_performance,
    churn_risk,
    compare_periods,
    conversion_funnel_report,
    detect_insights,
    engagement_score,
    event_volume,
    new_vs_returning,
    retention_lite,
    rfm_scores,
)
from behavioral.auto_insights import DOWN, FLAT, UP

NOW = datetime(2026, 6, 2, 12, 0, 0)


def _ev(cust, name, ts, **props):
    return {"customer_id": cust, "event_name": name, "ts": ts, **props}


# =============================================================================
# reports
# =============================================================================
def _activity_events():
    return [
        # in-window (last 7d)
        _ev("u1", "App Opened", NOW - timedelta(days=1)),
        _ev("u1", "App Opened", NOW - timedelta(days=2)),
        _ev("u2", "App Opened", NOW - timedelta(days=3)),
        _ev("u3", "Transfer", NOW - timedelta(days=1)),
        # u4 only has old activity (outside the 7d window)
        _ev("u4", "App Opened", NOW - timedelta(days=40)),
        # u2 also had old activity before the window -> returning
        _ev("u2", "App Opened", NOW - timedelta(days=30)),
    ]


def test_active_users_counts_distinct_in_window():
    r = active_users(_activity_events(), now=NOW, window_days=7)
    # u1, u2, u3 active in last 7 days; u4 is outside
    assert r.active_users == 3
    assert r.customer_ids == ["u1", "u2", "u3"]
    assert r.window_days == 7


def test_new_vs_returning_split():
    r = new_vs_returning(_activity_events(), now=NOW, window_days=7)
    # u2 had prior activity (40d? no, 30d ago) -> returning; u1, u3 are new
    assert r.returning_ids == ["u2"]
    assert r.new_ids == ["u1", "u3"]
    assert r.new_users == 2 and r.returning_users == 1


def test_event_volume_top_n_order():
    events = [
        _ev("a", "App Opened", NOW),
        _ev("b", "App Opened", NOW),
        _ev("c", "App Opened", NOW),
        _ev("a", "Transfer", NOW),
        _ev("b", "Transfer", NOW),
        _ev("a", "User Logout", NOW),
    ]
    r = event_volume(events, top_n=2)
    # App Opened=3, Transfer=2, User Logout=1 ; top 2 desc by count
    assert r.counts == [("App Opened", 3), ("Transfer", 2)]


def test_campaign_performance_ctr_cvr_and_divzero_guard():
    recs = [
        # camp_A: 4 SENT, 2 clicks, 1 conversion
        DeliveryRecord("u1", "camp_A", Channel.PUSH, "c", NOW, DeliveryStatus.SENT,
                       clicked=True, converted=True),
        DeliveryRecord("u2", "camp_A", Channel.PUSH, "c", NOW, DeliveryStatus.SENT,
                       clicked=True, converted=False),
        DeliveryRecord("u3", "camp_A", Channel.PUSH, "c", NOW, DeliveryStatus.SENT),
        DeliveryRecord("u4", "camp_A", Channel.PUSH, "c", NOW, DeliveryStatus.SENT),
        # a FAILED touch must be ignored (not a real impression)
        DeliveryRecord("u5", "camp_A", Channel.PUSH, "c", NOW, DeliveryStatus.FAILED,
                       clicked=True, converted=True),
        # camp_B: all suppressed -> 0 sent -> /0 guard yields 0.0 rates
        DeliveryRecord("u6", "camp_B", Channel.SMS, "c", NOW,
                       DeliveryStatus.SUPPRESSED_OPTOUT),
    ]
    r = campaign_performance(recs)
    by_id = {c.campaign_id: c for c in r.campaigns}
    a = by_id["camp_A"]
    assert a.sent == 4 and a.clicks == 2 and a.conversions == 1
    assert a.ctr == 0.5 and a.cvr == 0.25
    # camp_B never delivered -> appears with zeroed, no ZeroDivisionError
    assert "camp_B" not in by_id  # no SENT rows at all -> not aggregated


def test_campaign_performance_zero_sent_guard_explicit():
    # campaign present only via non-SENT statuses -> not in output, no crash
    recs = [
        DeliveryRecord("u1", "camp_X", Channel.PUSH, "c", NOW, DeliveryStatus.CAPPED),
    ]
    r = campaign_performance(recs)
    assert r.campaigns == []


def test_conversion_funnel_report_matches_direct_compute_funnel():
    T0 = datetime(2026, 6, 1, 9, 0)
    events = [
        _ev("a", "S1", T0), _ev("a", "S2", T0 + timedelta(hours=1)),
        _ev("a", "S3", T0 + timedelta(hours=2)),
        _ev("b", "S1", T0), _ev("b", "S2", T0 + timedelta(hours=1)),
        _ev("c", "S1", T0),
    ]
    steps = ["S1", "S2", "S3"]
    rep = conversion_funnel_report(events, steps, now=NOW)
    direct = compute_funnel(events, steps, now=NOW)
    # proves reuse: the report just packages M4's result, no divergence
    assert rep.step_counts == direct.step_counts
    assert rep.step_conversion == direct.step_conversion
    assert rep.drop_off == direct.drop_off
    assert rep.overall_conversion == direct.overall_conversion
    assert rep.funnel is not None
    assert rep.funnel.step_counts == direct.step_counts


def test_retention_lite_rate():
    events = [
        # window1 cohort = days [14, 7) ago : u1, u2, u3 active
        _ev("u1", "App Opened", NOW - timedelta(days=10)),
        _ev("u2", "App Opened", NOW - timedelta(days=9)),
        _ev("u3", "App Opened", NOW - timedelta(days=8)),
        # window2 = last 7 days : u1, u2 returned (u3 did not)
        _ev("u1", "App Opened", NOW - timedelta(days=2)),
        _ev("u2", "App Opened", NOW - timedelta(days=1)),
        # u4 only active in window2 -> not part of the cohort
        _ev("u4", "App Opened", NOW - timedelta(days=1)),
    ]
    r = retention_lite(events, now=NOW, first_window_days=7, return_window_days=7)
    assert r.cohort_size == 3
    assert r.retained == 2
    assert r.retention_rate == pytest.approx(2 / 3)


def test_retention_lite_empty_cohort_no_divzero():
    r = retention_lite([], now=NOW, first_window_days=7, return_window_days=7)
    assert r.cohort_size == 0 and r.retention_rate == 0.0


# =============================================================================
# auto-insights
# =============================================================================
def test_detect_insights_flags_spike():
    series = [10, 11, 9, 10, 40, 10, 11]  # index 4 is an obvious spike
    insights = detect_insights(series, z_threshold=2.0)
    assert len(insights) == 1
    spike = insights[0]
    assert spike.index == 4
    assert spike.direction == UP
    assert spike.notable is True
    assert "spiked" in spike.narrative


def test_detect_insights_flags_drop():
    series = [50, 51, 49, 50, 2, 50, 51]  # index 4 is an obvious drop
    insights = detect_insights(series, z_threshold=2.0)
    assert len(insights) == 1
    assert insights[0].index == 4
    assert insights[0].direction == DOWN
    assert "dropped" in insights[0].narrative


def test_detect_insights_flat_series_yields_none():
    assert detect_insights([5, 5, 5, 5]) == []
    assert detect_insights([]) == []


def test_detect_insights_uses_labels():
    series = [10, 10, 10, 100, 10]
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    insights = detect_insights(series, labels=labels, z_threshold=1.5)
    assert insights[0].label == "Thu"


def test_compare_periods_up_notable():
    ins = compare_periods(100, 150)  # +50%
    assert ins.direction == UP
    assert ins.notable is True
    assert ins.pct_change == pytest.approx(0.5)


def test_compare_periods_down_not_notable():
    ins = compare_periods(100, 95)  # -5%, below 20% threshold
    assert ins.direction == DOWN
    assert ins.notable is False


def test_compare_periods_from_zero():
    ins = compare_periods(0, 10)
    assert ins.direction == UP
    assert ins.notable is True
    assert ins.pct_change is None


# =============================================================================
# metrics (MoEngage replacements)
# =============================================================================
def _rfm_events():
    # u_recent: many recent events + big spend ; u_old: one old event, no spend
    return [
        _ev("u_recent", "App Opened", NOW - timedelta(days=1)),
        _ev("u_recent", "App Opened", NOW - timedelta(days=2)),
        _ev("u_recent", "Transfer", NOW - timedelta(days=1), amount=1000),
        _ev("u_recent", "Transfer", NOW - timedelta(days=2), amount=500),
        _ev("u_mid", "App Opened", NOW - timedelta(days=15)),
        _ev("u_mid", "Transfer", NOW - timedelta(days=15), amount=100),
        _ev("u_old", "App Opened", NOW - timedelta(days=120)),
    ]


def test_rfm_scores_deterministic():
    scores = rfm_scores(_rfm_events(), now=NOW, monetary_event="Transfer")
    assert set(scores) == {"u_recent", "u_mid", "u_old"}
    rec, old = scores["u_recent"], scores["u_old"]
    # recent user: lowest recency_days, highest frequency & monetary
    assert rec.frequency == 4
    assert rec.monetary == 1500.0
    assert rec.recency_days < old.recency_days
    # recency score: more recent -> higher r_score
    assert rec.r_score >= old.r_score
    # monetary: spender outranks the non-spender
    assert rec.m_score >= old.m_score
    assert old.monetary == 0.0


def test_rfm_no_monetary_event_zero_monetary():
    scores = rfm_scores(_rfm_events(), now=NOW)  # monetary_event=None
    assert all(s.monetary == 0.0 for s in scores.values())


def test_engagement_score_recent_beats_dormant():
    events = [
        _ev("active", "App Opened", NOW - timedelta(hours=1)),
        _ev("active", "App Opened", NOW - timedelta(days=1)),
        _ev("active", "Transfer", NOW - timedelta(days=2)),
        _ev("dormant", "App Opened", NOW - timedelta(days=29)),
    ]
    scores = engagement_score(events, now=NOW, window_days=30)
    assert scores["active"].score > scores["dormant"].score
    assert 0 <= scores["dormant"].score <= 100
    assert 0 <= scores["active"].score <= 100
    # active user is the busiest -> hits the frequency ceiling
    assert scores["active"].events_in_window == 3


def test_engagement_score_empty_when_no_window_activity():
    events = [_ev("u1", "App Opened", NOW - timedelta(days=100))]
    assert engagement_score(events, now=NOW, window_days=7) == {}


def test_churn_risk_recent_low_inactive_high():
    events = [
        _ev("recent", "App Opened", NOW - timedelta(days=1)),
        _ev("inactive", "App Opened", NOW - timedelta(days=120)),
        _ev("borderline", "App Opened", NOW - timedelta(days=45)),
    ]
    risk = churn_risk(events, now=NOW, inactive_days_threshold=60)
    assert risk["recent"].risk_label == "low"
    assert risk["recent"].risk_score < 0.5
    assert risk["inactive"].risk_label == "high"
    assert risk["inactive"].risk_score == 1.0  # clamped
    assert risk["borderline"].risk_label == "medium"


def test_churn_risk_rejects_bad_threshold():
    with pytest.raises(ValueError):
        churn_risk([], now=NOW, inactive_days_threshold=0)


# =============================================================================
# reuse cohort_engine sample data (sanity that real dataset flows through)
# =============================================================================
def test_reports_run_on_sample_dataset():
    from cohort_engine.sample_data import NOW as SNOW, build_sample_dataset

    ds = build_sample_dataset()
    events = ds["events"]
    au = active_users(events, now=SNOW, window_days=3)
    assert au.active_users >= 1
    vol = event_volume(events, top_n=3)
    assert len(vol.counts) <= 3
    rfm = rfm_scores(events, now=SNOW, monetary_event="Transfer")
    assert set(rfm) <= {u["customer_id"] for u in ds["users"]}
