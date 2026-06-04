"""Service: Personalization (M5 1-to-1 / Experiences).

Independently runnable::

    uvicorn services.personalization:app

Low-latency, app-facing decide-and-deliver service over an
:class:`ExperienceStore` + :class:`ExperienceService`, backed by the in-memory
demo world. The Botim app calls ``/experiences/fetch`` with user identifiers +
experience keys; growth-ops register / publish experiences out of band.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from cohort_engine.engine import CohortEngine
from personalization import (
    DEFAULT_LOCALE,
    Experience,
    ExperienceService,
    ExperienceStore,
    IdentifierError,
    Variation,
)

from ._world import NOW, build_world

app = FastAPI(title="Botim Growth — Personalization (M5)", version="0.1.0")

_WORLD = build_world()
_ENGINE = CohortEngine(_WORLD, now=NOW)
_STORE = ExperienceStore()
_SERVICE = ExperienceService(engine=_ENGINE, store=_STORE)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/experiences", status_code=201)
def register(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Register (draft) an experience: key, audience_spec, variations, control_pct."""
    key = payload.get("key")
    audience_spec = payload.get("audience_spec")
    variations_in = payload.get("variations")
    if not key or not isinstance(audience_spec, dict) or not isinstance(variations_in, list):
        raise HTTPException(
            status_code=422,
            detail="'key', 'audience_spec' (object) and 'variations' (list) are required",
        )
    try:
        variations = [
            Variation(
                name=v["name"],
                weight=float(v.get("weight", 1)),
                payload=v.get("payload", {}),
            )
            for v in variations_in
        ]
        exp = Experience(
            key=key,
            audience_spec=audience_spec,
            variations=variations,
            control_pct=float(payload.get("control_pct", 0.0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"invalid experience: {exc}") from exc
    _STORE.register(exp)
    return {"key": exp.key, "status": exp.status}


@app.post("/experiences/{key}/publish")
def publish(key: str) -> Dict[str, Any]:
    try:
        exp = _STORE.publish(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown experience '{key}'") from exc
    return {"key": exp.key, "status": exp.status}


@app.post("/experiences/fetch")
def fetch(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Decide + deliver content for the user across requested experience keys."""
    identifiers = payload.get("identifiers", {})
    keys: List[str] = payload.get("experience_keys", [])
    locale = payload.get("locale", DEFAULT_LOCALE)
    if not isinstance(keys, list) or not keys:
        raise HTTPException(status_code=422, detail="'experience_keys' (non-empty list) is required")
    try:
        payloads = _SERVICE.fetch(identifiers, keys, _WORLD, NOW, locale=locale)
    except IdentifierError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"experiences": payloads}
