"""Compile a Segment AST into SQL (M2 technical-solution B: compile-to-SQL).

Targets a generic ANSI-ish dialect (verified against ClickHouse / Doris style):
- users table:  users(customer_id, <attributes...>)
- events table: events(customer_id, event_name, ts, <properties...>)

The time window uses ``e.ts >= <now> - INTERVAL 'N' DAY``; adapt the INTERVAL
syntax per engine if needed. Event-property `where` clauses compile against the
events alias ``e``; time-dimension fields map to EXTRACT(... FROM e.ts).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import (
    AttributeCondition,
    EventCondition,
    Group,
    Node,
    Segment,
)

_OP_SQL = {"eq": "=", "ne": "<>", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
_TIME_DIM_SQL = {
    "hour_of_day": "EXTRACT(HOUR FROM e.ts)",
    "month_of_year": "EXTRACT(MONTH FROM e.ts)",
    "day_of_week": "EXTRACT(DOW FROM e.ts)",
}


class SqlCompileError(RuntimeError):
    pass


def _lit(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "NULL"
    # string: single-quote with escaping
    return "'" + str(value).replace("'", "''") + "'"


def _column(field: str, alias: str) -> str:
    # inside event `where`, time-dimension fields map to EXTRACT(...)
    if alias == "e" and field in _TIME_DIM_SQL:
        return _TIME_DIM_SQL[field]
    return f"{alias}.{field}"


def _attr_sql(cond: AttributeCondition, alias: str) -> str:
    col = _column(cond.field, alias)
    op = cond.operator
    if op == "exists":
        return f"{col} IS NOT NULL"
    if op == "not_exists":
        return f"{col} IS NULL"
    if op in _OP_SQL:
        return f"{col} {_OP_SQL[op]} {_lit(cond.value)}"
    if op == "in":
        return f"{col} IN ({', '.join(_lit(v) for v in cond.value)})"
    if op == "not_in":
        return f"{col} NOT IN ({', '.join(_lit(v) for v in cond.value)})"
    if op == "between":
        lo, hi = cond.value
        return f"{col} BETWEEN {_lit(lo)} AND {_lit(hi)}"
    if op == "contains":
        # string-substring match; escape LIKE wildcards to avoid pattern injection
        needle = str(cond.value).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"{col} LIKE {_lit('%' + needle + '%')} ESCAPE '\\'"
    raise SqlCompileError(f"unsupported attribute operator '{op}'")


def _where_sql(node: Node) -> str:
    """Compile an event `where` node against the events alias `e`."""
    if isinstance(node, AttributeCondition):
        return _attr_sql(node, "e")
    if isinstance(node, Group):
        return _group_sql(node, _where_sql)
    raise SqlCompileError("event 'where' may only contain attribute/group nodes")


def _count_subquery(cond: EventCondition, *, with_where: bool, now: datetime) -> str:
    parts = [
        "SELECT COUNT(*) FROM events e",
        f"WHERE e.customer_id = u.customer_id AND e.event_name = {_lit(cond.event)}",
    ]
    if cond.within_days is not None:
        parts.append(f"AND e.ts >= {_lit(_fmt_ts(now))} - INTERVAL '{cond.within_days}' DAY")
        parts.append(f"AND e.ts <= {_lit(_fmt_ts(now))}")
    if with_where and cond.where is not None:
        parts.append(f"AND ({_where_sql(cond.where)})")
    return "(" + " ".join(parts) + ")"


def _fmt_ts(now: datetime) -> str:
    return now.strftime("%Y-%m-%d %H:%M:%S")


def _event_sql(cond: EventCondition, now: datetime) -> str:
    matching = _count_subquery(cond, with_where=True, now=now)
    op = cond.frequency.op
    val = cond.frequency.value
    if op == "at_least":
        return f"{matching} >= {val}"
    if op == "at_most":
        return f"{matching} <= {val}"
    if op == "exactly":
        return f"{matching} = {val}"
    total = _count_subquery(cond, with_where=False, now=now)
    # wrap the whole compound predicate so it composes safely inside AND/OR/NOT groups
    if op == "min_percent":
        return f"(({total}) > 0 AND ({matching}) * 100.0 >= {val} * ({total}))"
    if op == "predominantly":
        return f"(({total}) > 0 AND ({matching}) * 2 > ({total}))"
    raise SqlCompileError(f"unsupported frequency op '{op}'")


def _group_sql(group: Group, child_sql) -> str:
    if group.op == "not":
        inner = " AND ".join(child_sql(c) for c in group.children)
        return f"NOT ({inner})"
    joiner = " AND " if group.op == "and" else " OR "
    return "(" + joiner.join(child_sql(c) for c in group.children) + ")"


def _node_sql(node: Node, now: datetime) -> str:
    if isinstance(node, AttributeCondition):
        return _attr_sql(node, "u")
    if isinstance(node, EventCondition):
        return _event_sql(node, now)
    if isinstance(node, Group):
        return _group_sql(node, lambda c: _node_sql(c, now))
    raise SqlCompileError(f"unknown node kind {type(node).__name__}")


def compile_segment(segment: Segment, now: datetime, *, count_only: bool = False) -> str:
    select = "COUNT(DISTINCT u.customer_id)" if count_only else "DISTINCT u.customer_id"
    where = _node_sql(segment.match, now)
    if segment.exclude is not None:
        where = f"({where}) AND NOT ({_node_sql(segment.exclude, now)})"
    return f"SELECT {select} FROM users u WHERE {where}"


def compile_count(segment: Segment, now: datetime) -> str:
    return compile_segment(segment, now, count_only=True)
