"""Frequency capping + cross-campaign dedup (M3).

Given prior ``DeliveryRecord`` history, ``FrequencyCapper`` enforces, per user:

* **daily cap** — at most ``daily_cap`` *sent* touches on the campaign run's
  calendar day (across all campaigns/channels);
* **cross-campaign dedup** — never message a user already touched by *this*
  campaign today (idempotent re-runs) — counts toward the same day.

Only ``SENT`` history consumes the daily budget (a capped/held-out/failed
record is not a delivered touch). Returns the allowed subset plus, for each
blocked user, a human-readable reason.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Iterable, List, Tuple

from growth_common import DeliveryRecord, DeliveryStatus


@dataclass
class CapResult:
    """Outcome of applying the frequency cap to a set of candidate users."""
    allowed: List[str] = field(default_factory=list)
    capped: Dict[str, str] = field(default_factory=dict)  # customer_id -> reason


class FrequencyCapper:
    def __init__(self, daily_cap: int = 1):
        if daily_cap < 1:
            raise ValueError("daily_cap must be >= 1")
        self.daily_cap = daily_cap

    def _today_index(
        self, history: Iterable[DeliveryRecord], today: date
    ) -> Tuple[Dict[str, int], set]:
        """Per-user count of sent touches today + set of (user) touched by
        each campaign today is built by the caller; here we return the
        per-user daily sent count and the set of users touched today overall."""
        sent_today: Dict[str, int] = {}
        for r in history:
            if r.ts.date() != today:
                continue
            if r.status == DeliveryStatus.SENT:
                sent_today[r.customer_id] = sent_today.get(r.customer_id, 0) + 1
        return sent_today, set(sent_today)

    def filter(
        self,
        customer_ids: Iterable[str],
        history: Iterable[DeliveryRecord],
        now: datetime,
        *,
        campaign_id: str = "",
    ) -> CapResult:
        """Return the subset of ``customer_ids`` allowed to be messaged now.

        A user is capped when either they are already at/over ``daily_cap``
        sent touches today, or they were already touched by ``campaign_id``
        today (cross-campaign dedup / idempotent re-run).
        """
        today = now.date()
        history = list(history)

        sent_today: Dict[str, int] = {}
        campaign_today: set = set()
        for r in history:
            if r.ts.date() != today:
                continue
            if r.status != DeliveryStatus.SENT:
                continue
            sent_today[r.customer_id] = sent_today.get(r.customer_id, 0) + 1
            if campaign_id and r.campaign_id == campaign_id:
                campaign_today.add(r.customer_id)

        result = CapResult()
        seen_this_run: set = set()
        for cid in customer_ids:
            if cid in seen_this_run:
                # de-dup within the same candidate list
                continue
            seen_this_run.add(cid)
            if cid in campaign_today:
                result.capped[cid] = "already_touched_by_campaign_today"
            elif sent_today.get(cid, 0) >= self.daily_cap:
                result.capped[cid] = "daily_cap_reached"
            else:
                result.allowed.append(cid)
        return result


__all__ = ["FrequencyCapper", "CapResult"]
