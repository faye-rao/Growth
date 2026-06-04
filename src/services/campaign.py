"""Service: Campaign (M3 Orchestration + M1 Messaging).

Independently runnable::

    uvicorn services.campaign:app

Composes orchestration (audience resolution, A/B/n allocation, control hold-out,
frequency cap) on top of the **real** M1 messaging :class:`Gateway`. The demo
world doubles as a cohort dataset and a messaging dataset (push tokens etc.), so
``/campaigns/run`` segments, allocates and actually sends in one process.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException

from cohort_engine.engine import CohortEngine
from cohort_engine.parser import RuleParseError
from messaging import Gateway
from orchestration import Campaign, Schedule, Variant
from orchestration.runner import CampaignRunner

from ._world import HIGH_VALUE_SPEC, NOW, build_world

app = FastAPI(title="Botim Growth — Campaign (M3+M1)", version="0.1.0")

_WORLD = build_world()
_ENGINE = CohortEngine(_WORLD, now=NOW)
# real M1 gateway; w2 opted out, mirroring the e2e demo's reachability story.
_GATEWAY = Gateway(opt_out={"w2"})
_RUNNER = CampaignRunner(engine=_ENGINE, gateway=_GATEWAY)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/campaigns/run")
def run_campaign(payload: Dict[str, Any] = Body(default=None)) -> Dict[str, Any]:
    """Build a Campaign from the body, resolve audience, send, return a summary."""
    payload = payload or {}
    audience_spec = payload.get("audience_spec", HIGH_VALUE_SPEC)
    variants_in = payload.get(
        "variants", [{"name": "A", "weight": 1, "content_id": "welcome_a"}]
    )
    try:
        variants = [
            Variant(
                name=v["name"],
                weight=float(v.get("weight", 1)),
                content_id=v.get("content_id", "default"),
            )
            for v in variants_in
        ]
        schedule = Schedule(start=NOW, end=NOW, trigger_type="batch")
        campaign = Campaign(
            id=payload.get("id", "demo_campaign"),
            audience_spec=audience_spec,
            channel=payload.get("channel", "push"),
            variants=variants,
            control_pct=float(payload.get("control_pct", 0.0)),
            schedule=schedule,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"invalid campaign: {exc}") from exc

    try:
        result = _RUNNER.run(campaign, _WORLD, NOW)
    except RuleParseError as exc:
        raise HTTPException(status_code=422, detail=f"invalid audience rule: {exc}") from exc

    return {
        "campaign_id": result.campaign_id,
        "audience_size": result.audience_size,
        "eligible_size": result.eligible_size,
        "sent_count": result.sent_count,
        "sent_by_variant": result.sent_by_variant,
        "control_count": result.control_count,
        "capped_count": result.capped_count,
        "not_sent_count": result.not_sent_count,
        "balances": result.balances,
    }


@app.post("/messages/send")
def send_messages(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Direct M1 batch send (bypasses orchestration); returns per-status counts."""
    ids: List[str] = payload.get("customer_ids", [])
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="'customer_ids' (non-empty list) is required")
    channel = payload.get("channel", "push")
    content_id = payload.get("content_id", "default")
    records = _GATEWAY.send_batch(
        [str(c) for c in ids],
        channel,
        content_id,
        campaign_id=payload.get("campaign_id", "adhoc"),
        dataset=_WORLD,
        now=NOW,
    )
    counts: Dict[str, int] = {}
    for r in records:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {"total": len(records), "by_status": counts}
