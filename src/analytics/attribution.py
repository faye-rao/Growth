"""Campaign attribution (M4).

Credit conversion events back to the campaigns that touched the user. A
conversion is credited to a campaign when a **SENT** ``DeliveryRecord`` for the
same user precedes the conversion within ``window_hours``. Two models are
supported:

- ``last_touch``: credit the most-recent eligible SENT touch before the
  conversion (default; the industry standard for messaging).
- ``first_touch``: credit the earliest eligible SENT touch before the
  conversion.

Inputs reuse the shared contract: ``DeliveryRecord`` (touch log) and the event
record shape ``{"customer_id","event_name","ts", ...}`` for conversions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Sequence

from growth_common import DeliveryRecord, DeliveryStatus

Event = Mapping[str, Any]

LAST_TOUCH = "last_touch"
FIRST_TOUCH = "first_touch"
_MODELS = (LAST_TOUCH, FIRST_TOUCH)


@dataclass
class AttributionResult:
    """Outcome of an attribution run.

    Attributes:
        model: the attribution model used.
        conversions_per_campaign: campaign_id -> number of credited conversions.
        sent_per_campaign: campaign_id -> number of distinct users sent a SENT
            touch (the denominator for conversion rate).
        conversion_rate_per_campaign: campaign_id -> converted / sent (0.0 when
            a campaign sent nothing).
        total_conversions: total conversion events that received credit.
        unattributed: conversion events with no eligible SENT touch in window.
    """

    model: str
    conversions_per_campaign: Dict[str, int] = field(default_factory=dict)
    sent_per_campaign: Dict[str, int] = field(default_factory=dict)
    conversion_rate_per_campaign: Dict[str, float] = field(default_factory=dict)
    total_conversions: int = 0
    unattributed: int = 0


def attribute(
    delivery_records: Sequence[DeliveryRecord],
    conversion_events: Sequence[Event],
    *,
    window_hours: float,
    model: str = LAST_TOUCH,
) -> AttributionResult:
    """Attribute ``conversion_events`` to campaigns via their SENT touches.

    Args:
        delivery_records: the touch log (shared ``DeliveryRecord`` contract).
            Only records with ``status == SENT`` are eligible to attribute.
        conversion_events: events representing conversions
            (``{"customer_id","event_name","ts", ...}``).
        window_hours: a touch is eligible only if
            ``0 <= conversion.ts - touch.ts <= window_hours``.
        model: ``"last_touch"`` or ``"first_touch"``.

    Returns:
        AttributionResult with conversions and conversion rate per campaign.
    """
    if model not in _MODELS:
        raise ValueError(f"model must be one of {_MODELS}, got {model!r}")
    if window_hours < 0:
        raise ValueError("window_hours must be non-negative")

    window = timedelta(hours=window_hours)

    # SENT touches grouped per user, sorted ascending by ts.
    sent_by_user: Dict[str, List[DeliveryRecord]] = {}
    sent_users_per_campaign: Dict[str, set] = {}
    for rec in delivery_records:
        if rec.status != DeliveryStatus.SENT:
            continue
        sent_by_user.setdefault(rec.customer_id, []).append(rec)
        sent_users_per_campaign.setdefault(rec.campaign_id, set()).add(rec.customer_id)
    for recs in sent_by_user.values():
        recs.sort(key=lambda r: r.ts)

    conversions_per_campaign: Dict[str, int] = {
        c: 0 for c in sent_users_per_campaign
    }
    total = 0
    unattributed = 0

    for ev in conversion_events:
        cust = ev["customer_id"]
        conv_ts: datetime = ev["ts"]
        eligible = [
            r
            for r in sent_by_user.get(cust, [])
            if r.ts <= conv_ts and (conv_ts - r.ts) <= window
        ]
        if not eligible:
            unattributed += 1
            continue
        # eligible is sorted ascending by ts.
        chosen = eligible[0] if model == FIRST_TOUCH else eligible[-1]
        conversions_per_campaign[chosen.campaign_id] = (
            conversions_per_campaign.get(chosen.campaign_id, 0) + 1
        )
        total += 1

    sent_per_campaign = {
        c: len(users) for c, users in sent_users_per_campaign.items()
    }
    conversion_rate_per_campaign = {
        c: (conversions_per_campaign.get(c, 0) / sent_per_campaign[c])
        if sent_per_campaign[c]
        else 0.0
        for c in sent_per_campaign
    }

    return AttributionResult(
        model=model,
        conversions_per_campaign=conversions_per_campaign,
        sent_per_campaign=sent_per_campaign,
        conversion_rate_per_campaign=conversion_rate_per_campaign,
        total_conversions=total,
        unattributed=unattributed,
    )
