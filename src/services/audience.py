"""Service: Audience (M2 Cohort Engine).

Independently runnable::

    uvicorn services.audience:app

Re-wraps :class:`CohortEngine` (and the NL2SQL + template helpers) over the
in-memory demo world. Endpoints mirror ``cohort_engine.api`` but are framed as
a standalone audience microservice.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from cohort_engine import templates as T
from cohort_engine.engine import CohortEngine
from cohort_engine.nl2sql import translate
from cohort_engine.parser import RuleParseError

from ._world import NOW, build_world

app = FastAPI(title="Botim Growth — Audience (M2)", version="0.1.0")

_ENGINE = CohortEngine(build_world(), now=NOW)


def _safe_evaluate(spec: Dict[str, Any]) -> List[str]:
    try:
        return sorted(_ENGINE.evaluate(spec))
    except RuleParseError as exc:
        raise HTTPException(status_code=422, detail=f"invalid rule: {exc}") from exc


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/segments/evaluate")
def evaluate(spec: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ids = _safe_evaluate(spec)
    return {"size": len(ids), "customer_ids": ids}


@app.post("/segments/size")
def size(spec: Dict[str, Any] = Body(...)) -> Dict[str, int]:
    return {"size": len(_safe_evaluate(spec))}


@app.post("/segments/compile")
def compile_sql(spec: Dict[str, Any] = Body(...)) -> Dict[str, str]:
    try:
        sql = _ENGINE.compile_sql(spec)
    except RuleParseError as exc:
        raise HTTPException(status_code=422, detail=f"invalid rule: {exc}") from exc
    return {"sql": sql}


@app.post("/nl2sql")
def nl2sql(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    text = payload.get("text")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=422, detail="'text' (string) is required")
    res = translate(text)
    return {
        "text": res.text,
        "dsl": res.dsl,
        "confidence": res.confidence,
        "matched": res.matched,
        "unmatched": res.unmatched,
        "requires_review": res.requires_review,
    }


@app.get("/templates")
def list_templates() -> Dict[str, List[str]]:
    return {"templates": sorted(T.TEMPLATES)}
