"""Automated analysis — auto-insights (M9).

Lightweight, dependency-free statistical flagging of period-over-period
spikes/drops over a metric time series, plus a two-period comparison helper.
This is the "automated analysis" leg of M9: instead of an operator eyeballing a
chart, we surface a short narrative for each notable point.

No third-party deps — z-scores are computed with stdlib arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

UP = "up"
DOWN = "down"
FLAT = "flat"


@dataclass
class Insight:
    """One automated finding.

    Attributes:
        index: position in the series (or -1 for a standalone comparison).
        label: human label for the point (defaults to ``str(index)``).
        value: the metric value at this point.
        direction: ``"up"`` / ``"down"`` / ``"flat"``.
        z_score: z-score of the value vs the series mean (0.0 for comparisons).
        pct_change: relative change vs the prior point / baseline (None if N/A).
        notable: whether this finding crossed the flag threshold.
        narrative: short human-readable summary string.
    """

    index: int
    label: str
    value: float
    direction: str
    z_score: float
    pct_change: Optional[float]
    notable: bool
    narrative: str


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _pstdev(xs: Sequence[float], mean: float) -> float:
    if len(xs) < 2:
        return 0.0
    var = sum((x - mean) ** 2 for x in xs) / len(xs)
    return var ** 0.5


def _pct_change(curr: float, base: float) -> Optional[float]:
    if base == 0:
        return None
    return (curr - base) / base


def detect_insights(
    series: Sequence[float],
    *,
    labels: Optional[Sequence[str]] = None,
    z_threshold: float = 2.0,
) -> List[Insight]:
    """Flag points in ``series`` that deviate from the series mean.

    For each point we compute its z-score against the whole-series mean/stdev. A
    point is *notable* when ``abs(z) >= z_threshold``. ``direction`` reflects the
    point's value vs the mean (up if above, down if below, flat if equal).
    ``pct_change`` is measured vs the immediately preceding point.

    Returns one :class:`Insight` per **notable** point (in series order). A flat
    or near-flat series produces an empty list (stdev 0 -> no z-scores).
    """
    n = len(series)
    if n == 0:
        return []
    if labels is not None and len(labels) != n:
        raise ValueError("labels must be the same length as series")

    mean = _mean(series)
    stdev = _pstdev(series, mean)
    out: List[Insight] = []
    if stdev == 0.0:
        return out  # perfectly flat -> nothing stands out

    for i, value in enumerate(series):
        z = (value - mean) / stdev
        if abs(z) < z_threshold:
            continue
        label = labels[i] if labels is not None else str(i)
        direction = UP if value > mean else DOWN if value < mean else FLAT
        pct = _pct_change(value, series[i - 1]) if i > 0 else None
        pct_txt = f" ({pct:+.0%} vs prior)" if pct is not None else ""
        verb = "spiked" if direction == UP else "dropped"
        narrative = (
            f"{label}: {verb} to {value:g}{pct_txt}; "
            f"{abs(z):.1f}σ from mean {mean:g}"
        )
        out.append(
            Insight(
                index=i,
                label=label,
                value=float(value),
                direction=direction,
                z_score=z,
                pct_change=pct,
                notable=True,
                narrative=narrative,
            )
        )
    return out


def compare_periods(
    before: float,
    after: float,
    *,
    notable_pct: float = 0.20,
) -> Insight:
    """Compare two periods (e.g. last week vs this week).

    Computes the relative change, direction, and whether it is *notable*
    (``abs(pct_change) >= notable_pct``). When ``before == 0`` the change is
    undefined; any nonzero ``after`` is treated as notable growth.
    """
    pct = _pct_change(after, before)
    if pct is None:
        direction = UP if after > 0 else FLAT
        notable = after != 0
        change_txt = "from 0 (new activity)" if after > 0 else "no change (0 -> 0)"
        narrative = f"period-over-period: {change_txt}"
        return Insight(
            index=-1,
            label="period-over-period",
            value=float(after),
            direction=direction,
            z_score=0.0,
            pct_change=None,
            notable=notable,
            narrative=narrative,
        )

    direction = UP if pct > 0 else DOWN if pct < 0 else FLAT
    notable = abs(pct) >= notable_pct
    verb = "up" if direction == UP else "down" if direction == DOWN else "flat"
    narrative = (
        f"period-over-period: {verb} {abs(pct):.0%} "
        f"({before:g} -> {after:g})"
        + ("" if notable else " (within normal range)")
    )
    return Insight(
        index=-1,
        label="period-over-period",
        value=float(after),
        direction=direction,
        z_score=0.0,
        pct_change=pct,
        notable=notable,
        narrative=narrative,
    )
