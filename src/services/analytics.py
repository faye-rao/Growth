"""Service: Analytics (M4 Funnel/Attribution + M9 Behavioral reports/insights).

Independently runnable::

    uvicorn services.analytics:app

Funnels and attribution come from M4 (``analytics``); operator-facing reports
and auto-insights come from M9 (``behavioral``), which itself reuses M4's funnel
math. Backed by the in-memory demo world's events.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from analytics import attribute, compute_funnel, cross_product_funnel
from behavioral import (
    active_users,
    detect_insights,
    event_volume,
    new_vs_returning,
    retention_lite,
)
from growth_common import Channel, DeliveryRecord, DeliveryStatus

from ._world import NOW, build_world

app = FastAPI(title="Botim Growth — Analytics (M4+M9)", version="0.1.0")

_WORLD = build_world()
_EVENTS = _WORLD["events"]

# M9 reports dispatched by name; each takes the demo events + a few kwargs.
_REPORTS = {
    "active_users": lambda p: active_users(
        _EVENTS, now=NOW, window_days=int(p.get("window_days", 7))
    ),
    "new_vs_returning": lambda p: new_vs_returning(
        _EVENTS, now=NOW, window_days=int(p.get("window_days", 7))
    ),
    "event_volume": lambda p: event_volume(_EVENTS, top_n=int(p.get("top_n", 10))),
    "retention_lite": lambda p: retention_lite(
        _EVENTS,
        now=NOW,
        first_window_days=int(p.get("first_window_days", 7)),
        return_window_days=int(p.get("return_window_days", 7)),
    ),
}


def _dump(obj: Any) -> Any:
    return asdict(obj) if is_dataclass(obj) else obj


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/funnel")
def funnel(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    steps: List[str] = payload.get("steps", ["App Opened", "Transfer"])
    if not isinstance(steps, list) or not steps:
        raise HTTPException(status_code=422, detail="'steps' (non-empty list) is required")
    within = payload.get("within_days")
    if payload.get("cross_product"):
        result = cross_product_funnel(_EVENTS, steps, now=NOW, within_days=within)
    else:
        try:
            result = compute_funnel(_EVENTS, steps, now=NOW, within_days=within)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _dump(result)


@app.post("/attribution")
def attribution(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Attribute conversion events to campaigns from a supplied touch log."""
    raw_records: List[Dict[str, Any]] = payload.get("records", [])
    conversions: List[Dict[str, Any]] = payload.get("conversions", [])
    window_hours = float(payload.get("window_hours", 24))
    model = payload.get("model", "last_touch")
    records: List[DeliveryRecord] = []
    for r in raw_records:
        ts = r.get("ts")
        records.append(
            DeliveryRecord(
                customer_id=str(r.get("customer_id", "")),
                campaign_id=str(r.get("campaign_id", "")),
                channel=r.get("channel", Channel.PUSH),
                content_id=str(r.get("content_id", "")),
                ts=datetime.fromisoformat(ts) if isinstance(ts, str) else NOW,
                status=DeliveryStatus.SENT,
            )
        )
    conv = [
        {
            "customer_id": str(c.get("customer_id", "")),
            "event_name": c.get("event_name", "Transfer"),
            "ts": datetime.fromisoformat(c["ts"]) if isinstance(c.get("ts"), str) else NOW,
        }
        for c in conversions
    ]
    try:
        result = attribute(records, conv, window_hours=window_hours, model=model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _dump(result)


@app.post("/reports/{name}")
def report(name: str, payload: Dict[str, Any] = Body(default=None)) -> Dict[str, Any]:
    builder = _REPORTS.get(name)
    if builder is None:
        raise HTTPException(
            status_code=404,
            detail=f"unknown report '{name}'; available: {sorted(_REPORTS)}",
        )
    return _dump(builder(payload or {}))


@app.post("/insights")
def insights(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Flag spikes/drops in a numeric series (z-score based)."""
    series = payload.get("series")
    if not isinstance(series, list) or not series:
        raise HTTPException(status_code=422, detail="'series' (non-empty list of numbers) is required")
    try:
        found = detect_insights(
            [float(x) for x in series],
            labels=payload.get("labels"),
            z_threshold=float(payload.get("z_threshold", 2.0)),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"insights": [_dump(i) for i in found]}
