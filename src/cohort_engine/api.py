"""REST API for the Cohort engine (product-shaped surface over the core).

Endpoints:
  POST /segments/evaluate   -> matched customer_ids + size
  POST /segments/size       -> audience-size estimate only (M2-A6)
  POST /segments/compile    -> equivalent SQL (compile-to-SQL)
  POST /nl2sql              -> natural-language -> DSL + confidence (M2-B)
  GET  /templates           -> list high-frequency cohort templates (M2-D2)
  POST /templates/{name}    -> instantiate + evaluate a template

The engine is backed by the in-memory sample dataset for this MVP; swap
`get_engine` for an OLAP-backed implementation in production (solution B).

Requires the optional 'api' extra:  pip install -e ".[api]"
Run:  uvicorn cohort_engine.api:app --reload
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException

from . import templates as T
from .engine import CohortEngine
from .nl2sql import translate
from .parser import RuleParseError
from .sample_data import NOW, build_sample_dataset

app = FastAPI(title="Botim Growth — M2 Cohort Engine", version="0.2.0")

# In production, inject an OLAP-backed engine; here we use the sample dataset.
_ENGINE = CohortEngine(build_sample_dataset(), now=NOW)


def get_engine() -> CohortEngine:
    return _ENGINE


def _safe_evaluate(spec: Dict[str, Any]):
    try:
        ids = sorted(get_engine().evaluate(spec))
    except RuleParseError as exc:
        raise HTTPException(status_code=422, detail=f"invalid rule: {exc}") from exc
    return ids


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
        sql = get_engine().compile_sql(spec)
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


@app.post("/templates/{name}")
def run_template(name: str, params: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    try:
        spec = T.build(name, **(params or {}))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TypeError as exc:
        raise HTTPException(status_code=422, detail=f"bad params: {exc}") from exc
    ids = _safe_evaluate(spec)
    return {"name": spec["name"], "size": len(ids), "customer_ids": ids, "dsl": spec}
