"""Dedup middle-layer: never double-send a user while both systems run.

Shadow validation runs the new system and MoEngage **in parallel** on the same
audience. Without a guard, a user could be messaged by *both* systems on the same
day — a bad experience and a confounder for the comparison. ``DedupLedger`` is the
middle layer that records every intended send and blocks a second send to the same
user within the run/day.

``reconcile`` is the campaign-fire helper: given the intended targets of each arm,
it enforces that the two arms are **disjoint** (a user assigned to one arm is never
sent by the other) and that no user is sent twice, returning the actual send lists
plus the blocked set.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Set, Tuple


class DedupLedger:
    """Records intended sends and blocks repeats to the same user within a day/run.

    A "send" is keyed by ``(customer_id, day)``. The first ``allow`` for that key
    returns ``True`` and registers the send; subsequent calls return ``False``.
    """

    def __init__(self) -> None:
        self._seen: Set[Tuple[str, object]] = set()

    def allow(self, customer_id: str, day: object) -> bool:
        """Return ``True`` if this is the first send to ``customer_id`` on ``day``.

        Records the send as a side effect; a second call with the same
        ``(customer_id, day)`` returns ``False`` (already sent).
        """
        key = (customer_id, day)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def sent(self, customer_id: str, day: object) -> bool:
        """Read-only check: has ``customer_id`` already been sent on ``day``?"""
        return (customer_id, day) in self._seen


def reconcile(
    shadow_targets: Iterable[str],
    control_targets: Iterable[str],
    *,
    day: object = "run",
) -> Tuple[List[str], List[str], Set[str]]:
    """Enforce disjoint, single-send arms for a parallel shadow/control run.

    A user assigned to the shadow arm is sent only by the new system; everyone else
    is sent only by MoEngage (control). Any user appearing in *both* target lists is
    a double-send: it is kept on the shadow arm and blocked from control. Within each
    arm, repeats are also collapsed to a single send.

    Returns ``(shadow_send, control_send, blocked)`` where ``shadow_send`` and
    ``control_send`` are order-preserving, de-duplicated, and disjoint, and
    ``blocked`` is the set of users prevented from a second send.
    """
    ledger = DedupLedger()
    shadow_send: List[str] = []
    control_send: List[str] = []
    blocked: Set[str] = set()

    # shadow arm wins the user; record its sends first so control can't re-send.
    for cid in shadow_targets:
        if ledger.allow(cid, day):
            shadow_send.append(cid)
        else:
            blocked.add(cid)
    for cid in control_targets:
        if ledger.allow(cid, day):
            control_send.append(cid)
        else:
            blocked.add(cid)

    return shadow_send, control_send, blocked


__all__ = ["DedupLedger", "reconcile"]
