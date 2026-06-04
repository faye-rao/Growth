"""Wide-table builder — assemble the dataset downstream modules consume (M8 ours).

We join the data team's labels onto the user table and shape events into the
exact ``{"users": [...], "events": [...]}`` contract that the M2 ``CohortEngine``
(and M4 funnel) expect:

* a user record is ``{"customer_id": ..., <attribute>: <value>, ...}``
* an event record is ``{"customer_id": ..., "event_name": ..., "ts": datetime,
  <prop>: <value>, ...}``

``build_dataset`` is the one call orchestrators use; its output is fed straight
into ``CohortEngine(dataset).evaluate(rule)``.

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

# Event-table fields the engine reads as the event identity; everything else on a
# clean event is carried through as an event property usable by `where`.
_INTERNAL_FIELDS = {"event_id", "ts_utc", "reason"}


def build_user_table(users: Iterable[Dict[str, Any]],
                     labels: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Join data-team ``labels`` (customer_id -> attribute dict) onto ``users``.

    Existing user fields win over label fields only if the label is absent; the
    label set augments the user with T+1-derived tags (e.g. ``dormant``,
    ``is_kyc``). Users without labels pass through unchanged.
    """
    table: List[Dict[str, Any]] = []
    for user in users:
        merged = dict(user)
        cid = user.get("customer_id")
        label_set = labels.get(cid)
        if label_set:
            for key, value in label_set.items():
                merged.setdefault(key, value)
        table.append(merged)
    return table


def build_event_table(clean_events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Shape clean (ingested) events into the engine's event-record contract.

    Requires ``ts`` (Dubai-normalized) to already be present; drops ingestion-only
    bookkeeping fields while preserving event properties.
    """
    table: List[Dict[str, Any]] = []
    for ev in clean_events:
        record = {k: v for k, v in ev.items() if k not in _INTERNAL_FIELDS}
        table.append(record)
    return table


def build_dataset(users: Iterable[Dict[str, Any]],
                  labels: Dict[str, Dict[str, Any]],
                  clean_events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the full ``{"users": [...], "events": [...]}`` dataset.

    Output is directly consumable by ``cohort_engine.CohortEngine``.
    """
    return {
        "users": build_user_table(users, labels),
        "events": build_event_table(clean_events),
    }
