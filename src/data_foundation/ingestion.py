"""Event ingestion — the consumer/glue layer of M8 (our part).

The heavy T+1 cleaning is owned by the data team; here we only do the *light*
last-mile work needed to feed downstream modules (M2 segmentation, M4 funnel):

* validate each raw event against a simple ``schema`` (event_name -> required
  fields / types). Invalid events are **quarantined** (kept with a reason),
  never silently dropped.
* **dedup** by an idempotency key — ``event_id`` when present (authoritative),
  else the natural key ``(customer_id, event_name, ts_utc)``. Distinct events
  with different ``event_id``s are never collapsed.
* **normalize timestamps to Asia/Dubai (UTC+4)**: raw events carry a naive UTC
  ``ts_utc``; output ``ts`` = ``ts_utc`` + 4h. Dubai has no DST, so a fixed +4
  offset is correct and keeps us dependency-free.

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Type, Union

# Asia/Dubai is UTC+4 year-round (no daylight saving), so a fixed offset is exact.
DUBAI_OFFSET = timedelta(hours=4)

TypeSpec = Union[Type, Tuple[Type, ...]]
Schema = Dict[str, Dict[str, TypeSpec]]


def to_dubai(ts_utc: datetime) -> datetime:
    """Convert a naive UTC datetime to naive Asia/Dubai local time (UTC+4)."""
    return ts_utc + DUBAI_OFFSET


@dataclass
class IngestResult:
    """Outcome of an ingestion pass.

    * ``clean`` — validated, deduped, Dubai-normalized events.
    * ``quarantined`` — events that failed validation, each annotated with a
      ``reason`` (kept for inspection/replay, not dropped).
    * ``deduped`` — number of duplicate events collapsed away.
    """
    clean: List[Dict[str, Any]] = field(default_factory=list)
    quarantined: List[Dict[str, Any]] = field(default_factory=list)
    deduped: int = 0


def _idempotency_key(ev: Dict[str, Any]) -> Any:
    """The single key used to collapse duplicates.

    ``event_id`` is authoritative when present; only when it is absent do we fall
    back to the natural key ``(customer_id, event_name, ts_utc)``. We deliberately
    do NOT union both: two genuinely distinct events that happen to share a natural
    key (e.g. two ``Transfer``s in the same second with different amounts) carry
    different ``event_id``s and must both survive.
    """
    if ev.get("event_id") is not None:
        return ("id", ev["event_id"])
    return ("nk", ev.get("customer_id"), ev.get("event_name"), ev.get("ts_utc"))


def _validate(ev: Dict[str, Any], schema: Schema) -> str:
    """Return an empty string if valid, else a human-readable reason."""
    name = ev.get("event_name")
    if name not in schema:
        return f"unknown event_name '{name}'"
    if not isinstance(ev.get("ts_utc"), datetime):
        return "missing or non-datetime ts_utc"
    for fld, expected_type in schema[name].items():
        if fld not in ev or ev[fld] is None:
            return f"missing required field '{fld}'"
        # bool is a subclass of int; guard so amount=True isn't accepted as number
        value = ev[fld]
        if isinstance(value, bool) and bool not in _as_tuple(expected_type):
            return f"field '{fld}' has wrong type (got bool)"
        if not isinstance(value, expected_type):
            return f"field '{fld}' has wrong type (got {type(value).__name__})"
    return ""


def _as_tuple(t: TypeSpec) -> Tuple[Type, ...]:
    return t if isinstance(t, tuple) else (t,)


def ingest(raw_events: List[Dict[str, Any]], schema: Schema, now: datetime) -> IngestResult:
    """Validate, dedup and Dubai-normalize ``raw_events``.

    ``now`` is accepted for symmetry with the rest of the platform (and so the
    caller can stamp an ingestion time); the result itself is deterministic.
    """
    result = IngestResult()
    seen: set = set()

    for ev in raw_events:
        reason = _validate(ev, schema)
        if reason:
            quarantined = dict(ev)
            quarantined["reason"] = reason
            result.quarantined.append(quarantined)
            continue

        key = _idempotency_key(ev)
        if key in seen:
            result.deduped += 1
            continue
        seen.add(key)

        clean = dict(ev)
        clean["ts"] = to_dubai(ev["ts_utc"])  # Asia/Dubai (+4) local time
        result.clean.append(clean)

    return result
