"""Service: Data Platform (M8 Data Foundation).

Independently runnable::

    uvicorn services.data_platform:app

Wraps the M8 last-mile consumer/glue: identity resolution, the suppression
("already converted -> don't message") layer, light ingestion (validate /
dedup / Dubai-normalize) and data-quality checks. Backed by the in-memory demo
world; swap the dependencies for warehouse-backed ones in production.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from data_foundation import IdentityResolver, SuppressionList, ingest, run_dqc

from ._world import NOW, build_world

app = FastAPI(title="Botim Growth — Data Platform (M8)", version="0.1.0")

# --- in-memory backing state (demo) -----------------------------------------
_WORLD = build_world()
_RESOLVER = IdentityResolver()
# users w1, w5 already transferred (converted) in the demo world -> suppressed.
_SUPPRESSION = SuppressionList(converted=["w1", "w5"])

# A minimal ingestion schema for the demo (event_name -> required field types).
_SCHEMA: Dict[str, Dict[str, Any]] = {
    "Transfer": {"amount": (int, float)},
    "App Opened": {},
    "Call Made": {},
}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/identity/resolve")
def resolve(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Resolve a canonical id from identifiers (customer_id > phone > device_id)."""
    identifiers = payload.get("identifiers", payload)
    if not isinstance(identifiers, dict):
        raise HTTPException(status_code=422, detail="'identifiers' must be an object")
    canonical = _RESOLVER.resolve({k: str(v) for k, v in identifiers.items()})
    return {"canonical_id": canonical, "resolved": canonical is not None}


@app.post("/suppression/check")
def suppression_check(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Split candidate customer_ids into allowed vs suppressed (already converted)."""
    ids = payload.get("customer_ids")
    if not isinstance(ids, list):
        raise HTTPException(status_code=422, detail="'customer_ids' (list) is required")
    allowed, suppressed = _SUPPRESSION.filter([str(c) for c in ids])
    return {"allowed": allowed, "suppressed": suppressed}


@app.post("/ingest")
def ingest_events(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Validate / dedup / Dubai-normalize raw events; return per-bucket counts."""
    raw: List[Dict[str, Any]] = payload.get("events", [])
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="'events' (list) is required")
    # accept ISO-8601 ts_utc strings for transport convenience
    from datetime import datetime

    norm: List[Dict[str, Any]] = []
    for ev in raw:
        ev = dict(ev)
        ts = ev.get("ts_utc")
        if isinstance(ts, str):
            try:
                ev["ts_utc"] = datetime.fromisoformat(ts)
            except ValueError:
                pass  # left as-is -> quarantined by validation
        norm.append(ev)

    result = ingest(norm, _SCHEMA, now=NOW)
    return {
        "clean": len(result.clean),
        "quarantined": len(result.quarantined),
        "deduped": result.deduped,
        "quarantine_reasons": [q.get("reason") for q in result.quarantined],
    }


@app.get("/dqc")
def dqc() -> Dict[str, Any]:
    """Run light data-quality checks against the demo dataset."""
    report = run_dqc(
        _WORLD,
        now=NOW,
        thresholds={"null_rate": 0.0, "dup_rate": 0.0, "max_latency_hours": 24 * 365},
    )
    return {"ok": report.ok, "metrics": report.metrics, "alerts": report.alerts}
