"""Sequential funnel computation (M4).

A funnel is an ordered list of event names (``steps``). A user is counted at
step *k* only if they fired step1, step2, ..., stepk **in chronological order**
— each subsequent step's timestamp must be ``>=`` the previous matched step's
timestamp. Optionally the whole sequence must complete within ``within_days``
of the user's first step.

Reuses the shared event record shape from ``cohort_engine.sample_data``::

    {"customer_id": str, "event_name": str, "ts": datetime, **props}
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Sequence

Event = Mapping[str, Any]


@dataclass
class FunnelResult:
    """Outcome of a sequential funnel computation.

    Attributes:
        steps: the ordered step (event) names, as supplied.
        step_counts: number of distinct users who reached each step (in order).
        step_conversion: step-to-step conversion rate; ``step_conversion[k]`` is
            ``step_counts[k] / step_counts[k-1]`` (the rate of advancing from the
            previous step). ``step_conversion[0]`` is always ``1.0`` (entry).
        drop_off: number of users lost between the previous step and this one;
            ``drop_off[0]`` is ``0``.
        overall_conversion: ``step_counts[-1] / step_counts[0]`` (last / first),
            or ``0.0`` when no user entered the funnel.
    """

    steps: List[str]
    step_counts: List[int]
    step_conversion: List[float]
    drop_off: List[int]
    overall_conversion: float

    @property
    def entered(self) -> int:
        """Users who completed the first step (top of funnel)."""
        return self.step_counts[0] if self.step_counts else 0

    @property
    def completed(self) -> int:
        """Users who completed the final step (bottom of funnel)."""
        return self.step_counts[-1] if self.step_counts else 0


def _events_by_user(events: Sequence[Event]) -> Dict[str, List[Event]]:
    by_user: Dict[str, List[Event]] = {}
    for ev in events:
        by_user.setdefault(ev["customer_id"], []).append(ev)
    # stable sort by timestamp so "in order" comparisons are deterministic
    for evs in by_user.values():
        evs.sort(key=lambda e: e["ts"])
    return by_user


def _deepest_step(
    user_events: Sequence[Event],
    steps: Sequence[str],
    *,
    deadline: Optional[datetime],
) -> int:
    """Return how many ordered steps this one user completed (0..len(steps)).

    Greedy in-order match: for each step, find the earliest occurrence whose ts
    is ``>=`` the previously matched step's ts (and ``<= deadline`` if set). If a
    step can't be matched, the user stops at the current depth.
    """
    reached = 0
    prev_ts: Optional[datetime] = None
    for step_name in steps:
        match_ts: Optional[datetime] = None
        for ev in user_events:  # pre-sorted by ts ascending
            if ev["event_name"] != step_name:
                continue
            ts = ev["ts"]
            if prev_ts is not None and ts < prev_ts:
                continue  # out of order relative to the prior step
            if deadline is not None and ts > deadline:
                continue  # too late for the within_days window
            match_ts = ts
            break  # earliest valid occurrence wins
        if match_ts is None:
            break
        reached += 1
        prev_ts = match_ts
    return reached


def compute_funnel(
    events: Sequence[Event],
    steps: Sequence[str],
    *,
    now: datetime,
    within_days: Optional[int] = None,
) -> FunnelResult:
    """Compute a sequential funnel over ``events`` for the ordered ``steps``.

    Args:
        events: event records ``{"customer_id","event_name","ts", ...}``.
        steps: ordered list of event names defining the funnel.
        now: reference time (kept for API symmetry / future windowing).
        within_days: if set, the user's *first* step and every later step must
            occur within ``within_days`` days of that first step; sequences that
            complete later are not counted at the late step.

    Returns:
        FunnelResult with per-step user counts, conversion rates and drop-off.
    """
    if not steps:
        raise ValueError("steps must be a non-empty ordered list of event names")

    n_steps = len(steps)
    counts = [0] * n_steps
    by_user = _events_by_user(events)

    for user_events in by_user.values():
        # Determine the per-user deadline from their first step occurrence.
        deadline: Optional[datetime] = None
        if within_days is not None:
            first_step = steps[0]
            first_ts = next(
                (e["ts"] for e in user_events if e["event_name"] == first_step),
                None,
            )
            if first_ts is None:
                continue  # never entered the funnel
            deadline = first_ts + timedelta(days=within_days)

        reached = _deepest_step(user_events, steps, deadline=deadline)
        for k in range(reached):
            counts[k] += 1

    step_conversion: List[float] = []
    drop_off: List[int] = []
    for k in range(n_steps):
        if k == 0:
            step_conversion.append(1.0)
            drop_off.append(0)
        else:
            prev = counts[k - 1]
            step_conversion.append(counts[k] / prev if prev else 0.0)
            drop_off.append(prev - counts[k])

    overall = counts[-1] / counts[0] if counts[0] else 0.0

    return FunnelResult(
        steps=list(steps),
        step_counts=counts,
        step_conversion=step_conversion,
        drop_off=drop_off,
        overall_conversion=overall,
    )
