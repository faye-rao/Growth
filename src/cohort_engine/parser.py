"""Parse & validate a JSON/dict rule spec into the Segment AST.

This is the entry point of the *MoEngage-syntax-compatible query layer* (M2-A7):
operations teams (or NL2SQL, later) emit a JSON DSL; this module turns it into a
validated AST that the evaluator and SQL compiler consume.
"""
from __future__ import annotations

from typing import Any

from .models import (
    ATTR_OPERATORS,
    FREQ_OPS,
    GROUP_OPS,
    AttributeCondition,
    EventCondition,
    Frequency,
    Group,
    Node,
    Segment,
)

# operators that do not carry a value
_VALUELESS_OPS = {"exists", "not_exists"}
_LIST_OPS = {"in", "not_in"}


class RuleParseError(ValueError):
    """Raised when a rule spec is structurally invalid."""


def parse_segment(spec: dict) -> Segment:
    if not isinstance(spec, dict):
        raise RuleParseError("segment spec must be an object")
    if "match" not in spec:
        raise RuleParseError("segment spec must contain a 'match' node")
    name = spec.get("name", "unnamed-segment")
    match = parse_node(spec["match"])
    exclude = parse_node(spec["exclude"]) if spec.get("exclude") is not None else None
    return Segment(name=name, match=match, exclude=exclude)


def parse_node(d: Any, *, in_event_where: bool = False) -> Node:
    if not isinstance(d, dict):
        raise RuleParseError(f"node must be an object, got {type(d).__name__}")

    # group node: presence of "op" in GROUP_OPS
    if d.get("op") in GROUP_OPS:
        return _parse_group(d, in_event_where=in_event_where)

    kind = d.get("type")
    if kind == "attribute":
        return _parse_attribute(d)
    if kind == "event":
        if in_event_where:
            raise RuleParseError("event conditions are not allowed inside an event 'where' clause")
        return _parse_event(d)

    raise RuleParseError(
        f"cannot determine node type from keys {sorted(d.keys())}; "
        "expected a group ('op') or {'type': 'attribute'|'event'}"
    )


def _parse_group(d: dict, *, in_event_where: bool) -> Group:
    op = d["op"]
    children = d.get("children")
    if not isinstance(children, list) or not children:
        raise RuleParseError(f"group '{op}' must have a non-empty 'children' list")
    return Group(op=op, children=[parse_node(c, in_event_where=in_event_where) for c in children])


def _parse_attribute(d: dict) -> AttributeCondition:
    field = d.get("field")
    operator = d.get("operator")
    if not field or not isinstance(field, str):
        raise RuleParseError("attribute condition requires a string 'field'")
    if operator not in ATTR_OPERATORS:
        raise RuleParseError(f"unknown attribute operator '{operator}'; allowed: {sorted(ATTR_OPERATORS)}")

    value = d.get("value")
    if operator in _VALUELESS_OPS:
        value = None
    elif operator in _LIST_OPS:
        if not isinstance(value, list):
            raise RuleParseError(f"operator '{operator}' requires a list 'value'")
    elif operator == "between":
        if not (isinstance(value, list) and len(value) == 2):
            raise RuleParseError("operator 'between' requires a 2-element list 'value'")
    else:
        if "value" not in d:
            raise RuleParseError(f"operator '{operator}' requires a 'value'")
    return AttributeCondition(field=field, operator=operator, value=value)


def _parse_event(d: dict) -> EventCondition:
    event = d.get("event")
    if not event or not isinstance(event, str):
        raise RuleParseError("event condition requires a string 'event'")

    freq_raw = d.get("frequency")
    if not isinstance(freq_raw, dict) or freq_raw.get("op") not in FREQ_OPS:
        raise RuleParseError(f"event condition requires 'frequency.op' in {sorted(FREQ_OPS)}")
    freq_op = freq_raw["op"]
    freq_val = freq_raw.get("value")
    if freq_op in {"at_least", "at_most", "exactly", "min_percent"}:
        if not isinstance(freq_val, (int, float)) or isinstance(freq_val, bool):
            raise RuleParseError(f"frequency op '{freq_op}' requires a numeric 'value'")
        if freq_op == "min_percent" and not (0 <= freq_val <= 100):
            raise RuleParseError("'min_percent' value must be between 0 and 100")
    # 'predominantly' takes no value

    within_days = d.get("within_days")
    if within_days is not None and (not isinstance(within_days, int) or within_days <= 0):
        raise RuleParseError("'within_days' must be a positive integer when present")

    where = parse_node(d["where"], in_event_where=True) if d.get("where") is not None else None

    return EventCondition(
        event=event,
        frequency=Frequency(op=freq_op, value=freq_val),
        within_days=within_days,
        where=where,
    )
