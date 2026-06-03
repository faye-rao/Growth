"""Cross-product-line funnel (M4 differentiator).

This is the analysis **MoEngage can't answer**: a single funnel whose steps
span *different Botim product lines* — e.g. Call -> Wallet -> Remittance::

    ["Call Active", "Wallet Register", "Remittance First Txn"]

MoEngage (and most messaging-analytics suites) scope funnels to events within
one product/app surface and cannot stitch a user's journey across independently
instrumented product lines into one ordered conversion funnel. Because our
event log is unified on ``customer_id`` (the shared event shape from
``cohort_engine.sample_data``), we can treat cross-product events as ordinary
ordered funnel steps and reuse :func:`analytics.funnel.compute_funnel`
unchanged. This thin wrapper exists to name and document that capability — it
adds no new semantics beyond ``compute_funnel``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from .funnel import FunnelResult, compute_funnel

Event = Mapping[str, Any]


def cross_product_funnel(
    events: Sequence[Event],
    product_steps: Sequence[str],
    *,
    now: datetime,
    within_days: Optional[int] = None,
) -> FunnelResult:
    """Compute an ordered funnel whose steps span different product lines.

    Identical semantics to :func:`analytics.funnel.compute_funnel`: each step is
    an event name, the user must fire them in chronological order, and the whole
    journey may be constrained to ``within_days`` of the first step. The only
    difference is intent — the steps deliberately cross product boundaries
    (Call / Wallet / Remittance), which is the cross-sell journey MoEngage can't
    report on.

    Args:
        events: unified event log keyed by ``customer_id`` across all products.
        product_steps: ordered event names spanning different product lines,
            e.g. ``["Call Active", "Wallet Register", "Remittance First Txn"]``.
        now: reference time (passed through to ``compute_funnel``).
        within_days: optional window from the first step (cross-sell horizon).

    Returns:
        FunnelResult for the cross-product journey.
    """
    return compute_funnel(events, product_steps, now=now, within_days=within_days)
