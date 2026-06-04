"""Near-real-time suppression layer — "already converted -> don't message" (M8 ours).

Downstream messaging (M1) and orchestration (M3) already enforce opt-out and
frequency caps; this is the growth-side complement: a fast set of customer_ids
that have *already converted*, so a campaign never re-targets a user who has
done the very thing the campaign is trying to drive.

Built from a stream/batch of conversion events; ``filter`` splits a target list
into ``(kept, suppressed)`` preserving input order.

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set, Tuple


class SuppressionList:
    """An immutable-ish set of already-converted customer_ids."""

    def __init__(self, converted: Iterable[str] = ()) -> None:
        self._converted: Set[str] = {c for c in converted if c}

    @classmethod
    def from_conversions(cls, conversion_events: Iterable[Dict[str, Any]]) -> "SuppressionList":
        """Build from conversion events (each carrying a ``customer_id``)."""
        return cls(ev.get("customer_id") for ev in conversion_events)

    def contains(self, customer_id: str) -> bool:
        return customer_id in self._converted

    def add(self, customer_id: str) -> None:
        """Add a freshly-converted user (supports near-real-time updates)."""
        if customer_id:
            self._converted.add(customer_id)

    def filter(self, customer_ids: Iterable[str]) -> Tuple[List[str], List[str]]:
        """Split ``customer_ids`` into ``(kept, suppressed)`` in input order."""
        kept: List[str] = []
        suppressed: List[str] = []
        for cid in customer_ids:
            (suppressed if cid in self._converted else kept).append(cid)
        return kept, suppressed

    def __len__(self) -> int:
        return len(self._converted)

    def __contains__(self, customer_id: object) -> bool:
        return customer_id in self._converted
