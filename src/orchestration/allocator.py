"""Deterministic control hold-out + A/B/n variant allocation.

Uses ``growth_common.stable_fraction(campaign_id, customer_id)`` so a given
user always lands in the same bucket across runs/processes (unlike ``hash()``).

Layout of the [0, 1) line for a campaign::

    [0 ............ control_pct) [control_pct ............................. 1)
    |<-- control group -------->|<-- variants, by normalized weight ------>|

The same fraction is reused for both the control decision and the variant
choice, so allocation is fully reproducible from (campaign_id, customer_id).
"""
from __future__ import annotations

from typing import Dict, Iterable, List

from growth_common import stable_fraction

from .models import Campaign, Variant

CONTROL = "control"


def _variant_cumulative(variants: List[Variant]) -> List[tuple[float, str]]:
    """Return cumulative-upper-bound -> variant_name breakpoints in [0, 1]."""
    total = sum(v.weight for v in variants)
    bounds: List[tuple[float, str]] = []
    acc = 0.0
    for v in variants:
        acc += v.weight / total
        bounds.append((acc, v.name))
    # guard against float drift on the last boundary
    bounds[-1] = (1.0, variants[-1].name)
    return bounds


def assign(campaign: Campaign, customer_id: str) -> str:
    """Bucket a single user into ``"control"`` or a variant name (stable)."""
    frac = stable_fraction(campaign.id, customer_id)
    if frac < campaign.control_pct:
        return CONTROL
    # rescale the remaining [control_pct, 1) span onto [0, 1) for the split
    span = 1.0 - campaign.control_pct
    rel = (frac - campaign.control_pct) / span if span > 0 else 0.0
    for upper, name in _variant_cumulative(campaign.variants):
        if rel < upper:
            return name
    return campaign.variants[-1].name  # unreachable (rel < 1.0), safe fallback


def allocate(campaign: Campaign, customer_ids: Iterable[str]) -> Dict[str, str]:
    """Allocate each user to ``"control"`` or a variant name.

    Deterministic: identical inputs always yield the identical mapping.
    """
    return {cid: assign(campaign, cid) for cid in customer_ids}


__all__ = ["allocate", "assign", "CONTROL"]
