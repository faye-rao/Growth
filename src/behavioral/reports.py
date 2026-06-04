"""Canonical "actually-viewed" operator reports (M9).

These are the ~6 reports operators open day-to-day — not a BI tool. Each is a
pure function over the shared event log shape
(``{"customer_id","event_name","ts", ...}`` — same as ``cohort_engine`` / M4)
or over the shared ``DeliveryRecord`` touch log, and returns a small structured
dataclass so callers (and tests) get stable fields.

The conversion-funnel report is a **thin wrapper over M4 ``compute_funnel``** —
M9 does not reimplement funnel logic.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from growth_common import DeliveryRecord, DeliveryStatus

from analytics import FunnelResult, compute_funnel

Event = Mapping[str, Any]


# --- active users -------------------------------------------------------------
@dataclass
class ActiveUsersReport:
    window_days: int
    active_users: int
    customer_ids: List[str]


def active_users(
    events: Sequence[Event], *, now: datetime, window_days: int
) -> ActiveUsersReport:
    """Distinct users with at least one event in ``[now - window_days, now]``."""
    start = now - timedelta(days=window_days)
    ids = {
        ev["customer_id"]
        for ev in events
        if start <= ev["ts"] <= now
    }
    return ActiveUsersReport(
        window_days=window_days,
        active_users=len(ids),
        customer_ids=sorted(ids),
    )


# --- new vs returning ---------------------------------------------------------
@dataclass
class NewVsReturningReport:
    window_days: int
    new_users: int
    returning_users: int
    new_ids: List[str]
    returning_ids: List[str]


def new_vs_returning(
    events: Sequence[Event], *, now: datetime, window_days: int
) -> NewVsReturningReport:
    """Split in-window active users by prior activity.

    A user active in the window is **returning** if they had any activity
    *before* the window started, otherwise **new**.
    """
    start = now - timedelta(days=window_days)
    active: set = set()
    had_prior: set = set()
    for ev in events:
        ts = ev["ts"]
        cust = ev["customer_id"]
        if start <= ts <= now:
            active.add(cust)
        elif ts < start:
            had_prior.add(cust)
    new_ids = sorted(c for c in active if c not in had_prior)
    returning_ids = sorted(c for c in active if c in had_prior)
    return NewVsReturningReport(
        window_days=window_days,
        new_users=len(new_ids),
        returning_users=len(returning_ids),
        new_ids=new_ids,
        returning_ids=returning_ids,
    )


# --- event volume -------------------------------------------------------------
@dataclass
class EventVolumeReport:
    top_n: int
    counts: List[Tuple[str, int]]  # ordered desc by count, then name


def event_volume(events: Sequence[Event], *, top_n: int = 10) -> EventVolumeReport:
    """Counts per ``event_name`` (top N, ties broken by name for determinism)."""
    counter: Counter = Counter(ev["event_name"] for ev in events)
    ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return EventVolumeReport(top_n=top_n, counts=ordered[:top_n])


# --- campaign performance -----------------------------------------------------
@dataclass
class CampaignStats:
    campaign_id: str
    sent: int
    clicks: int
    conversions: int
    ctr: float  # clicks / sent
    cvr: float  # conversions / sent


@dataclass
class CampaignPerformanceReport:
    campaigns: List[CampaignStats]  # ordered by campaign_id


def campaign_performance(
    delivery_records: Sequence[DeliveryRecord],
) -> CampaignPerformanceReport:
    """Per-campaign sent / clicks / conversions and CTR / CVR.

    Only ``SENT`` records count (a suppressed/failed touch was never delivered),
    so CTR/CVR denominators are real impressions. Divide-by-zero is guarded —
    a campaign with zero SENT yields ``0.0`` rates.
    """
    agg: dict = {}
    for rec in delivery_records:
        if rec.status != DeliveryStatus.SENT:
            continue
        s = agg.setdefault(
            rec.campaign_id, {"sent": 0, "clicks": 0, "conversions": 0}
        )
        s["sent"] += 1
        if rec.clicked:
            s["clicks"] += 1
        if rec.converted:
            s["conversions"] += 1

    campaigns: List[CampaignStats] = []
    for cid in sorted(agg):
        s = agg[cid]
        sent = s["sent"]
        campaigns.append(
            CampaignStats(
                campaign_id=cid,
                sent=sent,
                clicks=s["clicks"],
                conversions=s["conversions"],
                ctr=(s["clicks"] / sent) if sent else 0.0,
                cvr=(s["conversions"] / sent) if sent else 0.0,
            )
        )
    return CampaignPerformanceReport(campaigns=campaigns)


# --- conversion funnel report (REUSES M4 compute_funnel) ----------------------
@dataclass
class ConversionFunnelReport:
    steps: List[str]
    step_counts: List[int]
    step_conversion: List[float]
    drop_off: List[int]
    overall_conversion: float
    funnel: FunnelResult  # the raw M4 result, for callers that want it


def conversion_funnel_report(
    events: Sequence[Event],
    steps: Sequence[str],
    *,
    now: datetime,
    within_days: Optional[int] = None,
) -> ConversionFunnelReport:
    """Operator-facing funnel report — a thin wrapper over M4 ``compute_funnel``.

    Packages the :class:`analytics.FunnelResult` into a report dataclass; the
    numbers are produced entirely by M4 (no divergent funnel logic here).
    """
    fr = compute_funnel(events, steps, now=now, within_days=within_days)
    return ConversionFunnelReport(
        steps=fr.steps,
        step_counts=fr.step_counts,
        step_conversion=fr.step_conversion,
        drop_off=fr.drop_off,
        overall_conversion=fr.overall_conversion,
        funnel=fr,
    )


# --- retention (lite) ---------------------------------------------------------
@dataclass
class RetentionReport:
    first_window_days: int
    return_window_days: int
    cohort_size: int        # users active in window 1
    retained: int           # of those, active in window 2
    retention_rate: float   # retained / cohort_size


def retention_lite(
    events: Sequence[Event],
    *,
    now: datetime,
    first_window_days: int,
    return_window_days: int,
) -> RetentionReport:
    """Share of the window-1 cohort that returned in window 2.

    - Window 1 (the cohort): ``[now - (w1+w2), now - w2]`` — the earlier window.
    - Window 2 (the return window): ``(now - w2, now]`` — the most recent days.

    A user is *retained* if they were active in window 1 **and** active in
    window 2. Divide-by-zero guarded (empty cohort -> 0.0).
    """
    w2_start = now - timedelta(days=return_window_days)
    w1_start = w2_start - timedelta(days=first_window_days)

    cohort: set = set()
    returned: set = set()
    for ev in events:
        ts = ev["ts"]
        cust = ev["customer_id"]
        if w1_start <= ts < w2_start:
            cohort.add(cust)
        elif w2_start <= ts <= now:
            returned.add(cust)

    retained = cohort & returned
    rate = (len(retained) / len(cohort)) if cohort else 0.0
    return RetentionReport(
        first_window_days=first_window_days,
        return_window_days=return_window_days,
        cohort_size=len(cohort),
        retained=len(retained),
        retention_rate=rate,
    )
