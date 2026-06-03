"""M3 orchestration data models — campaign / variant / schedule definitions.

A ``Campaign`` ties together an M2 cohort rule DSL (``audience_spec``), a
delivery channel, an A/B/n variant split, an optional control hold-out and a
schedule (batch vs. event-triggered). Zero third-party dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# schedule trigger kinds
BATCH = "batch"
TRIGGERED = "triggered"
TRIGGER_TYPES = (BATCH, TRIGGERED)


@dataclass
class Variant:
    """One content arm of an A/B/n test.

    ``weight`` is a relative weight (need not sum to 1 across variants — the
    allocator normalizes). ``content_id`` is the template/content delivered.
    """
    name: str
    weight: float
    content_id: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("variant name must be non-empty")
        if self.weight <= 0:
            raise ValueError(f"variant '{self.name}' weight must be positive")


@dataclass
class Schedule:
    """When a campaign runs. ``batch`` = whole audience at send time;
    ``triggered`` = only users who fired ``trigger_event``."""
    start: datetime
    end: datetime
    trigger_type: str
    trigger_event: Optional[str] = None

    def __post_init__(self) -> None:
        if self.trigger_type not in TRIGGER_TYPES:
            raise ValueError(
                f"trigger_type must be one of {TRIGGER_TYPES}, got {self.trigger_type!r}"
            )
        if self.trigger_type == TRIGGERED and not self.trigger_event:
            raise ValueError("triggered schedule requires a trigger_event")

    @property
    def is_triggered(self) -> bool:
        return self.trigger_type == TRIGGERED


@dataclass
class Campaign:
    """A full campaign definition.

    ``audience_spec`` is a cohort rule DSL dict (same shape as M2 —
    ``CohortEngine.evaluate`` consumes it). ``control_pct`` (0..1) is held out
    as a control group; the remaining users are split across ``variants`` by
    weight.
    """
    id: str
    audience_spec: Dict[str, Any]
    channel: str
    variants: List[Variant]
    schedule: Schedule
    control_pct: float = 0.0
    goals: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("campaign id must be non-empty")
        if not (0.0 <= self.control_pct < 1.0):
            raise ValueError("control_pct must be in [0, 1)")
        if not self.variants:
            raise ValueError("campaign needs at least one variant")
        names = [v.name for v in self.variants]
        if len(names) != len(set(names)):
            raise ValueError("variant names must be unique")
        if "control" in names:
            raise ValueError("'control' is a reserved bucket name")


__all__ = [
    "Variant",
    "Schedule",
    "Campaign",
    "BATCH",
    "TRIGGERED",
    "TRIGGER_TYPES",
]
