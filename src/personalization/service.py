"""ExperienceService — the ``/v1/experiences/fetch`` decide-and-deliver core.

Given user identifiers + requested experience key(s), for each key it:

1. resolves the ``customer_id`` from the identifiers,
2. **gates** on publish state (missing / not-published -> ``None``),
3. checks **audience hit** via the M2 ``CohortEngine``,
4. assigns control / variation **deterministically** from
   ``stable_fraction(experience.key, customer_id)`` (same layout as
   ``orchestration.allocator``: a control hold-out prefix, then a
   weight-normalized variation split over the remaining span),
5. returns the chosen variation's payload for the requested ``locale``
   (falling back to the ``"default"`` locale), or ``None`` for control /
   non-audience / gated users.

The app renders the returned payload itself. Zero third-party deps.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from growth_common import stable_fraction

from cohort_engine import CohortEngine

from .models import DEFAULT_LOCALE, Experience, Variation
from .store import ExperienceStore

CONTROL = "control"

# identifier keys we accept, in resolution priority order. MoEngage-style
# identifiers map to a single internal customer_id.
_ID_KEYS = ("customer_id", "u_mb", "u_em")


class IdentifierError(ValueError):
    """Raised when no usable customer identifier is present."""


def resolve_customer_id(identifiers: Dict[str, Any]) -> Optional[str]:
    """Resolve a customer_id from identifiers, or ``None`` if absent.

    Prefers an explicit ``customer_id``; falls back to ``u_mb`` (mobile) /
    ``u_em`` (email) so the app can call with whatever identity it holds.
    """
    if not isinstance(identifiers, dict):
        return None
    for k in _ID_KEYS:
        v = identifiers.get(k)
        if v:
            return str(v)
    return None


def _variation_cumulative(variations: List[Variation]) -> List[tuple[float, str]]:
    """Cumulative-upper-bound -> variation_name breakpoints in [0, 1]."""
    total = sum(v.weight for v in variations)
    bounds: List[tuple[float, str]] = []
    acc = 0.0
    for v in variations:
        acc += v.weight / total
        bounds.append((acc, v.name))
    bounds[-1] = (1.0, variations[-1].name)  # guard float drift on last bound
    return bounds


def assign(experience: Experience, customer_id: str) -> str:
    """Bucket a user into ``"control"`` or a variation name (stable).

    Mirrors ``orchestration.allocator.assign`` so the platform has one
    deterministic split semantics across modules.
    """
    frac = stable_fraction(experience.key, customer_id)
    if frac < experience.control_pct:
        return CONTROL
    span = 1.0 - experience.control_pct
    rel = (frac - experience.control_pct) / span if span > 0 else 0.0
    for upper, name in _variation_cumulative(experience.variations):
        if rel < upper:
            return name
    return experience.variations[-1].name  # unreachable (rel < 1.0), safe


class ExperienceService:
    """Decide-and-deliver service over a :class:`CohortEngine` + store."""

    def __init__(self, engine: CohortEngine, store: ExperienceStore) -> None:
        self.engine = engine
        self.store = store

    def fetch(
        self,
        identifiers: Dict[str, Any],
        experience_keys: List[str],
        dataset: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
        locale: str = DEFAULT_LOCALE,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Return ``{experience_key: payload | None}`` for each requested key.

        ``None`` means "no personalization" — the user is gated out, not in the
        audience, or held out as control. Unknown keys also map to ``None``.
        Raises :class:`IdentifierError` when no customer identifier is present.
        """
        customer_id = resolve_customer_id(identifiers)
        if customer_id is None:
            raise IdentifierError(
                "fetch requires a customer identifier "
                f"(one of {_ID_KEYS}); got keys "
                f"{sorted(identifiers) if isinstance(identifiers, dict) else identifiers}"
            )

        result: Dict[str, Optional[Dict[str, Any]]] = {}
        # cache audience evaluations per spec id within a single fetch call
        audience_cache: Dict[int, set] = {}
        for key in experience_keys:
            result[key] = self._resolve_one(
                key, customer_id, dataset, now, locale, audience_cache
            )
        return result

    def _resolve_one(
        self,
        key: str,
        customer_id: str,
        dataset: Optional[Dict[str, Any]],
        now: Optional[datetime],
        locale: str,
        audience_cache: Dict[int, set],
    ) -> Optional[Dict[str, Any]]:
        exp = self.store.get(key)
        # gating: missing or not published -> no content
        if exp is None or not exp.is_published:
            return None

        # audience hit (cache identical spec objects within this fetch)
        spec_id = id(exp.audience_spec)
        audience = audience_cache.get(spec_id)
        if audience is None:
            audience = self.engine.evaluate(exp.audience_spec, dataset, now)
            audience_cache[spec_id] = audience
        if customer_id not in audience:
            return None

        # deterministic control / variation assignment
        bucket = assign(exp, customer_id)
        if bucket == CONTROL:
            return None  # held out, no personalization
        variation = next(v for v in exp.variations if v.name == bucket)
        return variation.payload_for(locale)


__all__ = ["ExperienceService", "resolve_customer_id", "assign", "CONTROL",
           "IdentifierError"]
