"""In-memory evaluation of a Segment against a dataset (M2-A5 batch evaluation).

Dataset shape::

    {
      "users":  [{"customer_id": "u1", <attr>: <val>, ...}, ...],
      "events": [{"customer_id": "u1", "event_name": "X", "ts": datetime, <prop>: <val>}, ...],
    }

`evaluate_segment` returns the set of matching customer_ids. Audience-size
estimation (M2-A6) is simply the size of that set (see engine.CohortEngine).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Set

from .models import (
    TIME_DIMENSION_FIELDS,
    AttributeCondition,
    EventCondition,
    Group,
    Node,
    Segment,
)


class EvaluationError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# attribute predicate (used for user records and for event records in `where`)
# --------------------------------------------------------------------------- #
def _eval_attribute(cond: AttributeCondition, record: Dict[str, Any]) -> bool:
    op = cond.operator
    present = cond.field in record and record[cond.field] is not None
    if op == "exists":
        return present
    if op == "not_exists":
        return not present

    actual = record.get(cond.field)
    if actual is None:
        # a missing value can never satisfy a positive comparison
        return False

    expected = cond.value
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "between":
        lo, hi = expected
        return lo <= actual <= hi
    if op == "contains":
        try:
            return expected in actual
        except TypeError:
            return False
    raise EvaluationError(f"unsupported attribute operator '{op}'")


# --------------------------------------------------------------------------- #
# event predicate
# --------------------------------------------------------------------------- #
def _event_record(ev: Dict[str, Any]) -> Dict[str, Any]:
    """Project an event into a record usable by `where`, deriving time dimensions."""
    rec = dict(ev)
    ts = ev.get("ts")
    if isinstance(ts, datetime):
        rec["hour_of_day"] = ts.hour
        rec["month_of_year"] = ts.month
        rec["day_of_week"] = ts.weekday()  # 0 = Monday
    return rec


def _eval_where(node: Optional[Node], event_record: Dict[str, Any]) -> bool:
    if node is None:
        return True
    if isinstance(node, AttributeCondition):
        return _eval_attribute(node, event_record)
    if isinstance(node, Group):
        return _eval_group(node, _make_event_where_evaluator(event_record))
    raise EvaluationError("event 'where' may only contain attribute/group nodes")


def _make_event_where_evaluator(event_record: Dict[str, Any]):
    def _ev(n: Node) -> bool:
        return _eval_where(n, event_record)
    return _ev


def _eval_event(cond: EventCondition, events: List[Dict[str, Any]], now: datetime) -> bool:
    name = cond.event
    lower = now - timedelta(days=cond.within_days) if cond.within_days is not None else None

    window: List[Dict[str, Any]] = []
    for ev in events:
        if ev.get("event_name") != name:
            continue
        ts = ev.get("ts")
        if lower is not None:
            # within a time window an event must carry a usable timestamp inside it
            # (matches the SQL compiler, which filters on e.ts unconditionally)
            if not isinstance(ts, datetime) or not (lower <= ts <= now):
                continue
        window.append(ev)

    total = len(window)
    if cond.where is None:
        matching = total
    else:
        matching = sum(1 for ev in window if _eval_where(cond.where, _event_record(ev)))

    op = cond.frequency.op
    val = cond.frequency.value
    if op == "at_least":
        return matching >= val
    if op == "at_most":
        return matching <= val
    if op == "exactly":
        return matching == val
    if op == "min_percent":
        return total > 0 and (matching * 100.0) >= (val * total)
    if op == "predominantly":
        return total > 0 and (matching * 2) > total
    raise EvaluationError(f"unsupported frequency op '{op}'")


# --------------------------------------------------------------------------- #
# group / node dispatch
# --------------------------------------------------------------------------- #
def _eval_group(group: Group, eval_child) -> bool:
    if group.op == "and":
        return all(eval_child(c) for c in group.children)
    if group.op == "or":
        return any(eval_child(c) for c in group.children)
    if group.op == "not":
        return not all(eval_child(c) for c in group.children)
    raise EvaluationError(f"unsupported group op '{group.op}'")


def _eval_node(node: Node, user: Dict[str, Any], events: List[Dict[str, Any]], now: datetime) -> bool:
    if isinstance(node, AttributeCondition):
        return _eval_attribute(node, user)
    if isinstance(node, EventCondition):
        return _eval_event(node, events, now)
    if isinstance(node, Group):
        return _eval_group(node, lambda c: _eval_node(c, user, events, now))
    raise EvaluationError(f"unknown node kind {type(node).__name__}")


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def _index_events(events: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_user: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        by_user.setdefault(ev["customer_id"], []).append(ev)
    return by_user


def evaluate_segment(segment: Segment, dataset: Dict[str, Any], now: datetime) -> Set[str]:
    users = dataset.get("users", [])
    events_by_user = _index_events(dataset.get("events", []))

    matched: Set[str] = set()
    for user in users:
        cid = user["customer_id"]
        ev = events_by_user.get(cid, [])
        if not _eval_node(segment.match, user, ev, now):
            continue
        if segment.exclude is not None and _eval_node(segment.exclude, user, ev, now):
            continue
        matched.add(cid)
    return matched
