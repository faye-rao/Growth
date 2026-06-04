"""M5 1-to-1 Personalization data models — experience / variation definitions.

Replicates MoEngage's *Experiences / Personalization* (``POST /v1/experiences/
fetch``): the Botim app calls with user identifiers + experience key(s); the
service decides which **experience + variation** the user qualifies for and
returns a **content payload**, which the app renders itself (the home-screen
"千人千面" card). Botim only borrows the "decide + deliver content" capability.

An ``Experience`` ties together an M2 cohort rule DSL (``audience_spec``), a set
of content ``variations`` (deterministic A/B/n split), an optional control
hold-out and a publish ``status`` that gates delivery. Zero third-party deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# publish lifecycle states
DRAFT = "draft"
PUBLISHED = "published"
PAUSED = "paused"
STATUSES = (DRAFT, PUBLISHED, PAUSED)

# locale used when a variation carries a flat (non-localized) payload, or when a
# requested locale is missing and we fall back.
DEFAULT_LOCALE = "default"


def _is_localized(payload: Dict[str, Any]) -> bool:
    """A payload is treated as localized if every value is itself a dict.

    ``{"en": {...}, "ar": {...}}`` -> localized;
    ``{"title": "Hi", "cta": "Go"}`` -> flat (wrapped under DEFAULT_LOCALE).
    """
    return bool(payload) and all(isinstance(v, dict) for v in payload.values())


@dataclass
class Variation:
    """One content arm of an experience.

    ``weight`` is a relative weight (need not sum to 1 across variations — the
    service normalizes). ``payload`` is either a localized map
    ``{locale: {key: value}}`` OR a flat ``{key: value}`` (treated as locale
    ``"default"``). It is normalized to the localized shape at construction.
    """
    name: str
    weight: float
    payload: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("variation name must be non-empty")
        if self.weight <= 0:
            raise ValueError(f"variation '{self.name}' weight must be positive")
        if not isinstance(self.payload, dict) or not self.payload:
            raise ValueError(f"variation '{self.name}' payload must be a non-empty dict")
        if not _is_localized(self.payload):
            # flat {key: value} -> wrap under the default locale
            self.payload = {DEFAULT_LOCALE: dict(self.payload)}

    def payload_for(self, locale: str = DEFAULT_LOCALE) -> Dict[str, Any]:
        """Return the payload for ``locale``, falling back to ``"default"``.

        Returns ``None`` only if neither the requested locale nor a default
        locale is present (which construction prevents for flat payloads).
        """
        if locale in self.payload:
            return self.payload[locale]
        return self.payload.get(DEFAULT_LOCALE)


@dataclass
class Experience:
    """A full personalization experience definition.

    ``audience_spec`` is a cohort rule DSL dict (same shape as M2 —
    ``CohortEngine.evaluate`` consumes it). ``control_pct`` (0..1) is held out
    as a control group (no personalization); the remaining users are split
    across ``variations`` by weight. ``status`` gates delivery: only
    ``"published"`` experiences ever return a payload.
    """
    key: str
    audience_spec: Dict[str, Any]
    variations: List[Variation]
    status: str = DRAFT
    control_pct: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("experience key must be non-empty")
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {self.status!r}")
        if not (0.0 <= self.control_pct < 1.0):
            raise ValueError("control_pct must be in [0, 1)")
        if not self.variations:
            raise ValueError("experience needs at least one variation")
        names = [v.name for v in self.variations]
        if len(names) != len(set(names)):
            raise ValueError("variation names must be unique")
        if "control" in names:
            raise ValueError("'control' is a reserved bucket name")

    @property
    def is_published(self) -> bool:
        return self.status == PUBLISHED


__all__ = [
    "Variation",
    "Experience",
    "DRAFT",
    "PUBLISHED",
    "PAUSED",
    "STATUSES",
    "DEFAULT_LOCALE",
]
