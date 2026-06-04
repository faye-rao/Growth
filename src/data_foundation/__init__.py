"""Botim Growth Platform — M8 Data Foundation (our part: consumer + glue).

The heavy T+1 data cleaning is owned by the data team. OUR scope is the
last-mile consumer/glue that feeds the growth modules:

* ``ingestion`` — validate (quarantine, don't drop) + dedup + normalize event
  timestamps to **Asia/Dubai (UTC+4, no DST -> fixed +4 offset)**.
* ``id_mapping`` — ``IdentityResolver`` over the data team's cross-line ID
  mapping; priority ``customer_id`` > ``phone`` > ``device_id`` (no email),
  union-find ``merge``, and resolution-coverage reporting.
* ``warehouse`` — join data-team labels onto users and build the wide
  ``{"users": [...], "events": [...]}`` dataset consumed directly by M2's
  ``CohortEngine`` (and M4 funnel).
* ``dqc`` — light data-quality checks (null_rate / dup_rate / freshness /
  row counts) with pass/fail alerts.
* ``suppression`` — near-real-time "already converted -> don't message" layer.

Public API::

    from data_foundation import ingest, IngestResult, to_dubai
    from data_foundation import IdentityResolver
    from data_foundation import build_user_table, build_event_table, build_dataset
    from data_foundation import run_dqc, DQCReport
    from data_foundation import SuppressionList

Zero third-party dependencies (stdlib only).
"""
from .dqc import DQCReport, run_dqc
from .id_mapping import IdentityResolver
from .ingestion import DUBAI_OFFSET, IngestResult, ingest, to_dubai
from .suppression import SuppressionList
from .warehouse import build_dataset, build_event_table, build_user_table

__all__ = [
    "ingest",
    "IngestResult",
    "to_dubai",
    "DUBAI_OFFSET",
    "IdentityResolver",
    "build_user_table",
    "build_event_table",
    "build_dataset",
    "run_dqc",
    "DQCReport",
    "SuppressionList",
]
__version__ = "0.1.0"
