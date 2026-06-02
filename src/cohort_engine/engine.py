"""CohortEngine facade — the single entry point for the M2 rule engine MVP.

Accepts a rule spec (dict JSON DSL or a pre-parsed Segment) and offers:
- evaluate(...)       -> matching customer_id set (M2-A5 batch evaluation)
- estimate_size(...)  -> audience size (M2-A6 real-time size estimation)
- compile_sql(...)    -> equivalent SQL (M2 solution B: compile-to-SQL)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Set, Union

from .models import Segment
from .parser import parse_segment
from .evaluator import evaluate_segment
from .sql_compiler import compile_segment, compile_count

SpecLike = Union[dict, Segment]


class CohortEngine:
    def __init__(self, dataset: Optional[Dict[str, Any]] = None, now: Optional[datetime] = None):
        """`dataset` and `now` are defaults; either can be overridden per call."""
        self.dataset = dataset or {"users": [], "events": []}
        self.now = now or datetime.utcnow()

    @staticmethod
    def _as_segment(spec: SpecLike) -> Segment:
        return spec if isinstance(spec, Segment) else parse_segment(spec)

    def evaluate(
        self,
        spec: SpecLike,
        dataset: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> Set[str]:
        return evaluate_segment(
            self._as_segment(spec),
            dataset if dataset is not None else self.dataset,
            now or self.now,
        )

    def estimate_size(
        self,
        spec: SpecLike,
        dataset: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> int:
        return len(self.evaluate(spec, dataset=dataset, now=now))

    def compile_sql(self, spec: SpecLike, now: Optional[datetime] = None) -> str:
        return compile_segment(self._as_segment(spec), now or self.now)

    def compile_count_sql(self, spec: SpecLike, now: Optional[datetime] = None) -> str:
        return compile_count(self._as_segment(spec), now or self.now)
