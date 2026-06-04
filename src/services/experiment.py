"""Service: Experiment (M7 Shadow Validation).

Independently runnable::

    uvicorn services.experiment:app

The acceptance gate for replacing MoEngage: deterministically split traffic into
a ``shadow`` (new system) vs ``control`` (MoEngage) arm — guaranteeing no user
is double-sent — then compare conversion on the two arms with a non-inferiority
verdict.
"""
from __future__ import annotations

from datetime import datetime
from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from growth_common import Channel, DeliveryRecord, DeliveryStatus
from shadow import compare, split

from ._world import NOW

app = FastAPI(title="Botim Growth — Experiment / Shadow (M7)", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/shadow/split")
def shadow_split(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Deterministically split customer_ids into shadow vs control arms."""
    ids: List[str] = payload.get("customer_ids", [])
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="'customer_ids' (non-empty list) is required")
    shadow_pct = float(payload.get("shadow_pct", 0.5))
    if not 0.0 <= shadow_pct <= 1.0:
        raise HTTPException(status_code=422, detail="'shadow_pct' must be in [0, 1]")
    assignment = split([str(c) for c in ids], shadow_pct=shadow_pct)
    shadow = sorted(c for c, arm in assignment.items() if arm == "shadow")
    control = sorted(c for c, arm in assignment.items() if arm == "control")
    return {"assignment": assignment, "shadow": shadow, "control": control}


def _records(raw: List[Dict[str, Any]]) -> List[DeliveryRecord]:
    out: List[DeliveryRecord] = []
    for r in raw:
        out.append(
            DeliveryRecord(
                customer_id=str(r.get("customer_id", "")),
                campaign_id=str(r.get("campaign_id", "shadow_exp")),
                channel=r.get("channel", Channel.PUSH),
                content_id=str(r.get("content_id", "c")),
                ts=NOW,
                status=DeliveryStatus.SENT,
                converted=bool(r.get("converted", False)),
            )
        )
    return out


@app.post("/shadow/report")
def shadow_report(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Compare control vs shadow conversion and emit a non-inferiority verdict."""
    control_in = payload.get("control_records", [])
    shadow_in = payload.get("shadow_records", [])
    if not isinstance(control_in, list) or not isinstance(shadow_in, list):
        raise HTTPException(
            status_code=422,
            detail="'control_records' and 'shadow_records' (lists) are required",
        )
    margin = float(payload.get("non_inferiority_margin", 0.0))
    report = compare(
        _records(control_in), _records(shadow_in), non_inferiority_margin=margin
    )
    return asdict(report)
