"""Service: Content (M6 AI Copywriting).

Independently runnable::

    uvicorn services.content:app

Generates multilingual marketing copy, runs the fintech compliance gate, and
picks the best-performing arm from delivery history. Backed by the deterministic
:class:`TemplateProvider` (a real LLM provider can be injected behind the same
interface in production).
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from copywriting import CopyGenerator, CopyRequest, TemplateProvider, check, select_best
from growth_common import Channel, DeliveryRecord, DeliveryStatus

app = FastAPI(title="Botim Growth — Content (M6)", version="0.1.0")

_GEN = CopyGenerator(TemplateProvider(), compliance_channel_default="push")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/copy/generate")
def generate(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Generate ``n`` compliant variants per requested locale."""
    goal = payload.get("goal")
    product = payload.get("product")
    locales = payload.get("locales")
    if not goal or not product or not isinstance(locales, list) or not locales:
        raise HTTPException(
            status_code=422,
            detail="'goal', 'product' and 'locales' (non-empty list) are required",
        )
    try:
        req = CopyRequest(
            goal=goal,
            product=product,
            locales=locales,
            tone=payload.get("tone", "friendly"),
            channel=payload.get("channel"),
            max_len=payload.get("max_len"),
        )
        variants = _GEN.generate(req, n=int(payload.get("n", 2)))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"invalid request: {exc}") from exc
    return {
        "variants": [
            {"locale": v.locale, "text": v.text, "meta": v.meta} for v in variants
        ]
    }


@app.post("/copy/compliance")
def compliance(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Run the fintech compliance gate over a piece of copy (auto-fix soft issues)."""
    text = payload.get("text")
    if not isinstance(text, str):
        raise HTTPException(status_code=422, detail="'text' (string) is required")
    res = check(text, channel=payload.get("channel"), product=payload.get("product"))
    return {"ok": res.ok, "violations": res.violations, "fixed_text": res.fixed_text}


@app.post("/copy/select-best")
def select_best_arm(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Pick the highest-CVR copy arm from a delivery/conversion history."""
    raw: List[Dict[str, Any]] = payload.get("records", [])
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="'records' (list) is required")
    records: List[DeliveryRecord] = []
    from datetime import datetime

    for r in raw:
        records.append(
            DeliveryRecord(
                customer_id=str(r.get("customer_id", "")),
                campaign_id=str(r.get("campaign_id", "")),
                channel=r.get("channel", Channel.PUSH),
                content_id=str(r.get("content_id", "")),
                ts=datetime.utcnow(),
                status=DeliveryStatus.SENT,
                variant=str(r.get("variant", "default")),
                converted=bool(r.get("converted", False)),
            )
        )
    return {"best": select_best(records)}
