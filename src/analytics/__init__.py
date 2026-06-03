"""M4 — Campaign Funnel Tracking & Attribution.

A self-built replacement for the funnel-analytics + attribution steps that
MoEngage charges for. Zero third-party dependencies (stdlib only).

Public API:
- `compute_funnel(events, steps, *, now, within_days=None) -> FunnelResult`
- `attribute(delivery_records, conversion_events, *, window_hours, model)
        -> AttributionResult`
- `cross_product_funnel(events, product_steps, *, now, within_days=None)`
  — the cross-product-line funnel differentiator (MoEngage can't answer this).
"""
from __future__ import annotations

from .attribution import AttributionResult, attribute
from .cross_product import cross_product_funnel
from .funnel import FunnelResult, compute_funnel

__all__ = [
    "compute_funnel",
    "FunnelResult",
    "attribute",
    "AttributionResult",
    "cross_product_funnel",
]
