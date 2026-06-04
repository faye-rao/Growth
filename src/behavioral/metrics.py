"""Self-built replacements for MoEngage internal metrics (M9).

When MoEngage is dropped, downstream consumers still expect RFM, engagement and
churn-risk signals it used to compute. This module reproduces them from our own
unified event log so nothing breaks. Pure stdlib, deterministic.

Event shape is the shared one: ``{"customer_id","event_name","ts", ...}``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Sequence

Event = Mapping[str, Any]


# --- RFM ----------------------------------------------------------------------
@dataclass
class RfmScore:
    customer_id: str
    recency_days: float        # days since last event (lower = more recent)
    frequency: int             # number of events
    monetary: float            # summed monetary_event amount (0 if none)
    r_score: int               # quintile 1..5 (5 = most recent)
    f_score: int               # quintile 1..5 (5 = most frequent)
    m_score: int               # quintile 1..5 (5 = highest monetary)


def _quintile_rank(value: float, sorted_values: List[float], *, higher_is_better: bool) -> int:
    """Map ``value`` to a 1..5 quintile score among ``sorted_values`` (ascending).

    Uses the value's percentile position so results are deterministic and don't
    depend on bucket-edge ties. ``higher_is_better`` flips the scale (used for
    recency, where a *lower* days-since-last is better).
    """
    n = len(sorted_values)
    if n == 0:
        return 1
    # percentile position: share of values <= this one, in (0, 1]
    below = sum(1 for v in sorted_values if v <= value)
    pct = below / n
    # map percentile to a 1..5 quintile (ceil(pct*5), clamped)
    score = min(5, max(1, -(-int(pct * 100) // 20)))
    if not higher_is_better:
        score = 6 - score
    return score


def rfm_scores(
    events: Sequence[Event],
    *,
    now: datetime,
    monetary_event: Optional[str] = None,
) -> Dict[str, RfmScore]:
    """Compute Recency / Frequency / Monetary (+ 1..5 quintile scores) per user.

    Args:
        events: the unified event log.
        now: reference time for recency.
        monetary_event: if given, only events with this ``event_name`` contribute
            to monetary value, summing their ``amount`` property. If ``None``,
            monetary is 0 for everyone (R/F only).

    Returns:
        ``customer_id -> RfmScore``. Quintile scores are relative to the user set
        (recency: more-recent -> higher r_score; frequency/monetary: higher raw
        -> higher score).
    """
    last_ts: Dict[str, datetime] = {}
    freq: Dict[str, int] = {}
    money: Dict[str, float] = {}
    for ev in events:
        cust = ev["customer_id"]
        ts = ev["ts"]
        freq[cust] = freq.get(cust, 0) + 1
        if cust not in last_ts or ts > last_ts[cust]:
            last_ts[cust] = ts
        if monetary_event is not None and ev["event_name"] == monetary_event:
            money[cust] = money.get(cust, 0.0) + float(ev.get("amount", 0) or 0)

    users = list(freq)
    recency = {u: (now - last_ts[u]).total_seconds() / 86400.0 for u in users}
    monetary = {u: money.get(u, 0.0) for u in users}

    rec_sorted = sorted(recency.values())
    freq_sorted = sorted(float(freq[u]) for u in users)
    mon_sorted = sorted(monetary.values())

    out: Dict[str, RfmScore] = {}
    for u in users:
        out[u] = RfmScore(
            customer_id=u,
            recency_days=recency[u],
            frequency=freq[u],
            monetary=monetary[u],
            # recency: lower days = better -> higher_is_better=False
            r_score=_quintile_rank(recency[u], rec_sorted, higher_is_better=False),
            f_score=_quintile_rank(float(freq[u]), freq_sorted, higher_is_better=True),
            m_score=_quintile_rank(monetary[u], mon_sorted, higher_is_better=True),
        )
    return out


# --- engagement ---------------------------------------------------------------
@dataclass
class EngagementScore:
    customer_id: str
    score: float  # 0..100
    recency_days: float
    events_in_window: int


def engagement_score(
    events: Sequence[Event], *, now: datetime, window_days: int
) -> Dict[str, EngagementScore]:
    """0..100 engagement per user from recency + frequency within the window.

    Score = ``0.5 * recency_component + 0.5 * frequency_component`` where:
      - recency_component (0..100) decays linearly from 100 (active today) to 0
        (last active ``window_days`` ago or earlier).
      - frequency_component (0..100) scales the user's in-window event count
        against the busiest user in the window (so the most active user gets
        100). Falls back to 0 when nobody was active.

    Only users with at least one in-window event get a score.
    """
    start = now - timedelta(days=window_days)
    last_ts: Dict[str, datetime] = {}
    freq: Dict[str, int] = {}
    for ev in events:
        ts = ev["ts"]
        if not (start <= ts <= now):
            continue
        cust = ev["customer_id"]
        freq[cust] = freq.get(cust, 0) + 1
        if cust not in last_ts or ts > last_ts[cust]:
            last_ts[cust] = ts

    out: Dict[str, EngagementScore] = {}
    if not freq:
        return out
    max_freq = max(freq.values())
    span = float(window_days) if window_days > 0 else 1.0
    for cust, count in freq.items():
        rec_days = (now - last_ts[cust]).total_seconds() / 86400.0
        recency_component = max(0.0, 100.0 * (1.0 - rec_days / span))
        frequency_component = 100.0 * (count / max_freq) if max_freq else 0.0
        score = round(0.5 * recency_component + 0.5 * frequency_component, 2)
        out[cust] = EngagementScore(
            customer_id=cust,
            score=score,
            recency_days=rec_days,
            events_in_window=count,
        )
    return out


# --- churn risk ---------------------------------------------------------------
LOW = "low"
MEDIUM = "medium"
HIGH = "high"


@dataclass
class ChurnRisk:
    customer_id: str
    recency_days: float
    risk_score: float  # 0..1 (higher = more likely to churn)
    risk_label: str    # low / medium / high


def churn_risk(
    events: Sequence[Event], *, now: datetime, inactive_days_threshold: int
) -> Dict[str, ChurnRisk]:
    """Risk label/score per user from inactivity (recency).

    ``risk_score`` is ``recency_days / inactive_days_threshold`` clamped to
    ``[0, 1]`` — a user inactive for the full threshold (or longer) scores 1.0.
    Labels: ``< 0.5`` low, ``< 1.0`` medium, ``>= 1.0`` high. A recently active
    user lands in **low**; a long-inactive user lands in **high**.
    """
    if inactive_days_threshold <= 0:
        raise ValueError("inactive_days_threshold must be positive")

    last_ts: Dict[str, datetime] = {}
    for ev in events:
        cust = ev["customer_id"]
        ts = ev["ts"]
        if cust not in last_ts or ts > last_ts[cust]:
            last_ts[cust] = ts

    out: Dict[str, ChurnRisk] = {}
    for cust, ts in last_ts.items():
        rec_days = (now - ts).total_seconds() / 86400.0
        score = min(1.0, max(0.0, rec_days / inactive_days_threshold))
        label = LOW if score < 0.5 else MEDIUM if score < 1.0 else HIGH
        out[cust] = ChurnRisk(
            customer_id=cust,
            recency_days=rec_days,
            risk_score=score,
            risk_label=label,
        )
    return out
