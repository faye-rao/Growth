"""Domain model (AST) for the Cohort rule DSL.

Mirrors MoEngage's segmentation rule engine (M2-A1~A3): nested AND/OR/NOT
groups, attribute conditions, and event conditions with frequency + time-window
+ event-property/time-dimension filters.

Zero third-party dependencies (stdlib dataclasses) to keep the core portable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

# --- operator vocabularies (single source of truth, reused by parser & SQL) ---
ATTR_OPERATORS = {
    "eq", "ne", "gt", "gte", "lt", "lte",
    "in", "not_in", "exists", "not_exists", "between", "contains",
}
FREQ_OPS = {"at_least", "at_most", "exactly", "min_percent", "predominantly"}
GROUP_OPS = {"and", "or", "not"}

# event-timestamp-derived fields usable inside an event `where` clause
TIME_DIMENSION_FIELDS = {"hour_of_day", "month_of_year", "day_of_week"}


@dataclass
class AttributeCondition:
    """A predicate on a user attribute (or, inside event.where, an event property)."""
    field: str
    operator: str
    value: Any = None
    kind: str = "attribute"


@dataclass
class Frequency:
    """How often an event must (not) have occurred."""
    op: str
    value: Optional[float] = None  # required for at_least/at_most/exactly/min_percent


@dataclass
class EventCondition:
    """A predicate on a user's event history (M2-A1 event condition + M2-A3 frequency)."""
    event: str
    frequency: Frequency
    within_days: Optional[int] = None          # M2-A2 time window
    where: Optional["Node"] = None             # event-property / time-dimension filter
    kind: str = "event"


@dataclass
class Group:
    """Logical composition of child nodes (M2-A1 infinite nesting).

    op == "not" means logical NOT of AND(children); for a single child it is a
    plain negation (e.g. "has NOT executed X").
    """
    op: str
    children: List["Node"]
    kind: str = "group"


Node = Union[AttributeCondition, EventCondition, Group]


@dataclass
class Segment:
    """A named cohort: users matching `match` minus users matching `exclude` (M2-A4)."""
    name: str
    match: Node
    exclude: Optional[Node] = None
