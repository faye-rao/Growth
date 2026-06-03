"""RoaringBitmap inverted-index audience engine (M2 technical-solution C).

Why this exists: at Botim's UAE scale (~2.5M users), the per-user in-memory
evaluator cannot answer audience-size queries interactively. This engine
pre-indexes users into an inverted index of RoaringBitmaps keyed by
(attribute, value); audience algebra becomes bitmap AND/OR/ANDNOT and
**audience-size estimation is an O(1)-ish bitmap cardinality** — milliseconds at
millions of users.

Scope: attribute conditions + nested AND/OR/NOT + exclude. Event conditions with
frequency/time-window are not directly bitmap-able; they are pre-computed at T+1
into **boolean tags** (merged into the user record as normal attributes, e.g.
``{"logout_ge2_dh5_3d": True}``) and then indexed/queried like any attribute.
Anything the index cannot serve (e.g. ``contains``, live event conditions) raises
``BitmapUnsupported`` so the caller can fall back to SQL / the in-memory evaluator.

Requires pyroaring:  pip install -e ".[bitmap]"
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

from pyroaring import BitMap

from .models import AttributeCondition, EventCondition, Group, Node, Segment
from .parser import parse_segment

TagFn = Callable[[Dict[str, Any], List[Dict[str, Any]]], bool]


class BitmapUnsupported(RuntimeError):
    """Raised when a condition cannot be served by the bitmap index."""


class BitmapIndex:
    """Inverted index: (field, value) -> RoaringBitmap of user ordinals."""

    def __init__(self) -> None:
        self.n = 0
        self.attr: Dict[str, Dict[Any, BitMap]] = {}
        self.present: Dict[str, BitMap] = {}
        self.ids: List[str] = []        # ordinal -> customer_id (optional)
        self._all: Optional[BitMap] = None

    def add(self, ordinal: int, record: Dict[str, Any], customer_id: Optional[str] = None) -> None:
        if customer_id is not None:
            self.ids.append(customer_id)
        self.n = max(self.n, ordinal + 1)
        for field, value in record.items():
            if value is None:
                continue
            self.present.setdefault(field, BitMap()).add(ordinal)
            self.attr.setdefault(field, {}).setdefault(value, BitMap()).add(ordinal)

    def finalize(self) -> "BitmapIndex":
        self._all = BitMap(range(self.n))
        return self

    @property
    def all_users(self) -> BitMap:
        if self._all is None:
            self.finalize()
        return self._all  # type: ignore[return-value]

    # --- node -> bitmap ---
    def _attr_bitmap(self, cond: AttributeCondition) -> BitMap:
        field, op, val = cond.field, cond.operator, cond.value
        values = self.attr.get(field, {})
        present = self.present.get(field, BitMap())

        if op == "exists":
            return present.copy()
        if op == "not_exists":
            return self.all_users - present
        if op == "eq":
            return values.get(val, BitMap()).copy()
        if op == "ne":
            return present - values.get(val, BitMap())
        if op == "in":
            out = BitMap()
            for v in val:
                out |= values.get(v, BitMap())
            return out
        if op == "not_in":
            out = BitMap()
            for v in val:
                out |= values.get(v, BitMap())
            return present - out
        if op in ("gt", "gte", "lt", "lte", "between"):
            return self._numeric_range(values, op, val)
        # contains and anything else: not indexable
        raise BitmapUnsupported(f"operator '{op}' is not bitmap-indexable (use SQL/evaluator)")

    @staticmethod
    def _numeric_range(values: Dict[Any, BitMap], op: str, val: Any) -> BitMap:
        out = BitMap()
        for v, bm in values.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            ok = (
                (op == "gt" and v > val) or
                (op == "gte" and v >= val) or
                (op == "lt" and v < val) or
                (op == "lte" and v <= val) or
                (op == "between" and val[0] <= v <= val[1])
            )
            if ok:
                out |= bm
        return out

    def _node_bitmap(self, node: Node) -> BitMap:
        if isinstance(node, AttributeCondition):
            return self._attr_bitmap(node)
        if isinstance(node, Group):
            return self._group_bitmap(node)
        if isinstance(node, EventCondition):
            raise BitmapUnsupported(
                f"event condition on '{node.event}' must be pre-computed into a boolean tag"
            )
        raise BitmapUnsupported(f"unknown node {type(node).__name__}")

    def _group_bitmap(self, group: Group) -> BitMap:
        if not group.children:
            return BitMap()
        bms = [self._node_bitmap(c) for c in group.children]
        if group.op == "and":
            acc = bms[0].copy()
            for b in bms[1:]:
                acc &= b
            return acc
        if group.op == "or":
            acc = BitMap()
            for b in bms:
                acc |= b
            return acc
        if group.op == "not":
            acc = bms[0].copy()
            for b in bms[1:]:
                acc &= b
            return self.all_users - acc
        raise BitmapUnsupported(f"unsupported group op '{group.op}'")

    def segment_bitmap(self, segment: Segment) -> BitMap:
        result = self._node_bitmap(segment.match)
        if segment.exclude is not None:
            result = result - self._node_bitmap(segment.exclude)
        return result


class BitmapAudienceEngine:
    """High-level facade: build the index once, then evaluate/estimate in ms."""

    def __init__(
        self,
        dataset: Optional[Dict[str, Any]] = None,
        tag_fns: Optional[Dict[str, TagFn]] = None,
        now: Optional[datetime] = None,
    ):
        self.index = BitmapIndex()
        self.tag_fns = tag_fns or {}
        self.now = now or datetime.utcnow()
        if dataset is not None:
            self.build(dataset)

    def build(self, dataset: Dict[str, Any]) -> "BitmapAudienceEngine":
        users = dataset.get("users", [])
        events_by_user: Dict[str, List[Dict[str, Any]]] = {}
        for ev in dataset.get("events", []):
            events_by_user.setdefault(ev["customer_id"], []).append(ev)

        for ordinal, user in enumerate(users):
            cid = user["customer_id"]
            record = {k: v for k, v in user.items() if k != "customer_id"}
            # merge pre-computed boolean tags (event-derived conditions)
            evs = events_by_user.get(cid, [])
            for tag, fn in self.tag_fns.items():
                record[tag] = bool(fn(user, evs))
            self.index.add(ordinal, record, customer_id=cid)
        self.index.finalize()
        return self

    @staticmethod
    def _as_segment(spec) -> Segment:
        return spec if isinstance(spec, Segment) else parse_segment(spec)

    def estimate_size(self, spec) -> int:
        """Audience size via bitmap cardinality (M2-A6, real-time at scale)."""
        return len(self.index.segment_bitmap(self._as_segment(spec)))

    def evaluate(self, spec) -> Set[str]:
        bm = self.index.segment_bitmap(self._as_segment(spec))
        return {self.index.ids[o] for o in bm}
