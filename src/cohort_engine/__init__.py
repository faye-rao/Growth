"""Botim Growth Platform — M2 Cohort Segmentation Rule Engine (MVP).

Public API::

    from cohort_engine import CohortEngine
    from cohort_engine.sample_data import build_sample_dataset, NOW

    engine = CohortEngine(build_sample_dataset(), now=NOW)
    ids = engine.evaluate(rule_spec)          # set of customer_id
    n   = engine.estimate_size(rule_spec)     # audience size
    sql = engine.compile_sql(rule_spec)       # equivalent SQL
"""
from .engine import CohortEngine
from .models import (
    AttributeCondition,
    EventCondition,
    Frequency,
    Group,
    Segment,
)
from .parser import RuleParseError, parse_segment

__all__ = [
    "CohortEngine",
    "Segment",
    "Group",
    "AttributeCondition",
    "EventCondition",
    "Frequency",
    "parse_segment",
    "RuleParseError",
]
__version__ = "0.1.0"
