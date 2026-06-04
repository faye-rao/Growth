"""Light data-quality checks over the assembled dataset (M8 ours).

The data team owns deep cleaning; our DQC is a fast, last-mile guardrail run
before the dataset is served to segmentation/funnel. Each check produces a
pass/fail against a threshold; failures land in ``report.alerts``.

Checks:

* ``null_rate``  — fraction of user records missing the primary key field.
* ``dup_rate``   — fraction of events that are idempotency-key duplicates.
* ``freshness``  — latency between ``now`` and the most recent event ``ts``.
* ``row_counts`` — informational user / event counts (never an alert).

Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DQCReport:
    """Result of a DQC pass.

    ``metrics`` holds every measured value; ``alerts`` holds only the failures
    (each ``{"check", "value", "threshold"}``). ``ok`` is True iff no alerts.
    """
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.alerts


def _event_key(ev: Dict[str, Any]) -> Any:
    if ev.get("event_id") is not None:
        return ("id", ev["event_id"])
    return ("nk", ev.get("customer_id"), ev.get("event_name"), ev.get("ts"))


def run_dqc(dataset: Dict[str, Any], now: datetime,
            thresholds: Dict[str, float], *, key_field: str = "customer_id") -> DQCReport:
    """Run light DQC checks on ``dataset`` and return a :class:`DQCReport`.

    ``thresholds`` may set ``null_rate`` (max), ``dup_rate`` (max) and
    ``max_latency_hours`` (max). Missing thresholds skip that check's alert.
    """
    report = DQCReport()
    users = dataset.get("users", [])
    events = dataset.get("events", [])

    # row counts (informational)
    report.metrics["user_count"] = len(users)
    report.metrics["event_count"] = len(events)

    # null_rate on the primary key field
    if users:
        nulls = sum(1 for u in users if u.get(key_field) in (None, ""))
        null_rate = nulls / len(users)
    else:
        null_rate = 0.0
    report.metrics["null_rate"] = null_rate
    _check(report, "null_rate", null_rate, thresholds.get("null_rate"), higher_is_worse=True)

    # dup_rate on the idempotency key
    if events:
        seen: set = set()
        dups = 0
        for ev in events:
            k = _event_key(ev)
            if k in seen:
                dups += 1
            else:
                seen.add(k)
        dup_rate = dups / len(events)
    else:
        dup_rate = 0.0
    report.metrics["dup_rate"] = dup_rate
    _check(report, "dup_rate", dup_rate, thresholds.get("dup_rate"), higher_is_worse=True)

    # freshness / latency = now - max(event ts), in hours
    latest = _max_ts(events)
    latency_hours: Optional[float]
    if latest is None:
        latency_hours = None
    else:
        latency_hours = (now - latest).total_seconds() / 3600.0
    report.metrics["latency_hours"] = latency_hours
    if latency_hours is not None:
        _check(report, "freshness", latency_hours,
               thresholds.get("max_latency_hours"), higher_is_worse=True)

    return report


def _max_ts(events: List[Dict[str, Any]]) -> Optional[datetime]:
    stamps = [ev["ts"] for ev in events if isinstance(ev.get("ts"), datetime)]
    return max(stamps) if stamps else None


def _check(report: DQCReport, name: str, value: float,
           threshold: Optional[float], *, higher_is_worse: bool) -> None:
    if threshold is None:
        return
    failed = value > threshold if higher_is_worse else value < threshold
    if failed:
        report.alerts.append({"check": name, "value": value, "threshold": threshold})
