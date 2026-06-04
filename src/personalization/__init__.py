"""Botim Growth Platform — M5 1-to-1 Personalization / content delivery (MVP).

A self-built replacement for MoEngage's *Experiences* / Personalization
(``POST /v1/experiences/fetch``): the Botim app calls with user identifiers +
experience key(s); the service **decides** which experience + variation the
user qualifies for and **delivers** a content payload, which the app renders
itself (the home-screen "千人千面" card).

Key behaviors:
- **audience hit** via the M2 cohort rule engine (``CohortEngine.evaluate``),
- **deterministic variation assignment** via ``growth_common.stable_fraction``
  (control hold-out + weighted split, same as ``orchestration.allocator``),
- **publish-state gating** — only ``published`` experiences return content,
- **multi-language payloads** — per-locale content with default fallback.

Public API::

    from personalization import Experience, Variation
    from personalization import ExperienceStore, ExperienceService

    store = ExperienceStore()
    store.register(Experience(
        key="home_card",
        audience_spec=rule_dsl,
        variations=[
            Variation("A", 1, {"en": {"title": "Hi"}, "ar": {"title": "مرحبا"}}),
            Variation("B", 1, {"title": "Hello"}),   # flat -> locale "default"
        ],
        control_pct=0.1,
    ))
    store.publish("home_card")

    service = ExperienceService(engine=cohort_engine, store=store)
    payloads = service.fetch({"customer_id": "u1"}, ["home_card"],
                             dataset, now, locale="ar")
    # -> {"home_card": {"title": "مرحبا"} | None}

Zero third-party dependencies (stdlib + the shared ``growth_common`` contract).
"""
from .models import (
    DEFAULT_LOCALE,
    DRAFT,
    PAUSED,
    PUBLISHED,
    STATUSES,
    Experience,
    Variation,
)
from .service import CONTROL, ExperienceService, IdentifierError, assign, resolve_customer_id
from .store import ExperienceStore

__all__ = [
    "Variation",
    "Experience",
    "ExperienceStore",
    "ExperienceService",
    "resolve_customer_id",
    "assign",
    "CONTROL",
    "IdentifierError",
    "DRAFT",
    "PUBLISHED",
    "PAUSED",
    "STATUSES",
    "DEFAULT_LOCALE",
]
__version__ = "0.1.0"
