"""Deterministic traffic splitter for shadow validation.

The acceptance gate for replacing MoEngage runs the new system on a small
traffic slice (e.g. 5%) **in parallel** with MoEngage on the *same* audience.
This module decides, per user, which arm they belong to::

    [0 ........... shadow_pct) [shadow_pct ........................... 1)
    |<-- "shadow" (new system) ->|<-- "control" (MoEngage) ----------->|

Uses ``growth_common.stable_fraction(salt, customer_id)`` so a given user always
lands in the same arm across runs/processes (unlike ``hash()``). This stability
is what makes the A/B comparison fair: the slice is fixed, not re-rolled.
"""
from __future__ import annotations

from typing import Dict, Iterable

from growth_common import stable_fraction

SHADOW = "shadow"
CONTROL = "control"


def assign_arm(customer_id: str, *, shadow_pct: float, salt: str = "shadow") -> str:
    """Bucket a single user into ``"shadow"`` (new system) or ``"control"`` (MoEngage).

    Deterministic and stable: identical ``(salt, customer_id)`` always yields the
    same arm. ``shadow_pct`` is a fraction in ``[0, 1]`` (e.g. ``0.05`` for 5%).
    """
    return SHADOW if stable_fraction(salt, customer_id) < shadow_pct else CONTROL


def split(customer_ids: Iterable[str], shadow_pct: float, *, salt: str = "shadow") -> Dict[str, str]:
    """Assign each user to ``"shadow"`` or ``"control"``.

    Deterministic: identical inputs always yield the identical mapping.
    """
    return {cid: assign_arm(cid, shadow_pct=shadow_pct, salt=salt) for cid in customer_ids}


__all__ = ["assign_arm", "split", "SHADOW", "CONTROL"]
