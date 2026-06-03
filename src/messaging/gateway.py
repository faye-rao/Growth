"""Gateway — the unified messaging收口 point (M1 core).

Every campaign sends through one ``Gateway`` so the delivery pipeline is applied
uniformly. Per user, in order:

1. **Opt-out** suppression                       → SUPPRESSED_OPTOUT
2. **Reachability filter** (the M1 differentiator) → SUPPRESSED_UNREACHABLE
3. **Rate limit** (token bucket)                  → FAILED (meta reason rate_limited)
4. **Adapter deliver** with multi-channel fallback (push→sms→in_app)
                                                   → SENT / FAILED

``send_batch`` returns one ``DeliveryRecord`` per user and also appends every
record to an internal ``log`` list. Implements the ``MessagingGateway`` protocol.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from growth_common import Channel, DeliveryRecord, DeliveryStatus

from .adapters import ChannelAdapter, PushAdapter, SmsAdapter, InAppAdapter
from .rate_limiter import RateLimiter
from .sample_data import STALE_AFTER_DAYS

# Fallback order: try the primary channel first, then the rest in this order.
_FALLBACK_ORDER = (Channel.PUSH, Channel.SMS, Channel.IN_APP)


class Gateway:
    def __init__(
        self,
        *,
        opt_out: Optional[Set[str]] = None,
        rate_limiter: Optional[RateLimiter] = None,
        adapters: Optional[Dict[str, ChannelAdapter]] = None,
        stale_after_days: int = STALE_AFTER_DAYS,
    ):
        self.opt_out: Set[str] = set(opt_out or set())
        self.rate_limiter = rate_limiter
        self.adapters: Dict[str, ChannelAdapter] = adapters or {
            Channel.PUSH: PushAdapter(),
            Channel.SMS: SmsAdapter(),
            Channel.IN_APP: InAppAdapter(),
        }
        self.stale_after_days = stale_after_days
        self.log: List[DeliveryRecord] = []

    # --- public API (MessagingGateway protocol) ------------------------------
    def send_batch(
        self,
        customer_ids: List[str],
        channel: str,
        content_id: str,
        *,
        campaign_id: str,
        dataset: Dict[str, Any],
        now: datetime,
        variant: str = "default",
    ) -> List[DeliveryRecord]:
        users = {u["customer_id"]: u for u in dataset.get("users", [])}
        records: List[DeliveryRecord] = []
        for cid in customer_ids:
            rec = self.send_one(
                cid,
                channel,
                content_id,
                campaign_id=campaign_id,
                user=users.get(cid, {"customer_id": cid}),
                now=now,
                variant=variant,
            )
            records.append(rec)
        return records

    def send_one(
        self,
        customer_id: str,
        channel: str,
        content_id: str,
        *,
        campaign_id: str,
        user: Dict[str, Any],
        now: datetime,
        variant: str = "default",
    ) -> DeliveryRecord:
        # 1) opt-out suppression
        if customer_id in self.opt_out:
            return self._record(customer_id, campaign_id, channel, content_id, now,
                                 DeliveryStatus.SUPPRESSED_OPTOUT, variant,
                                 meta={"reason": "opt_out"})

        # 2) reachability filter (M1 differentiator)
        reason = self._unreachable_reason(user, channel, now)
        if reason is not None:
            return self._record(customer_id, campaign_id, channel, content_id, now,
                                 DeliveryStatus.SUPPRESSED_UNREACHABLE, variant,
                                 meta={"reason": reason})

        # 3) rate limit
        if self.rate_limiter is not None and not self.rate_limiter.allow():
            return self._record(customer_id, campaign_id, channel, content_id, now,
                                 DeliveryStatus.FAILED, variant,
                                 meta={"reason": "rate_limited"})

        # 4) adapter deliver with multi-channel fallback
        return self._deliver_with_fallback(customer_id, campaign_id, channel,
                                           content_id, user, now, variant)

    # --- pipeline internals --------------------------------------------------
    def _unreachable_reason(
        self, user: Dict[str, Any], channel: str, now: datetime
    ) -> Optional[str]:
        if user.get("app_uninstalled"):
            return "app_uninstalled"
        if channel == Channel.PUSH and not user.get("push_token"):
            return "no_push_token"
        last_active = user.get("last_active")
        if isinstance(last_active, datetime):
            if now - last_active > timedelta(days=self.stale_after_days):
                return "stale_last_active"
        return None

    def _deliver_with_fallback(
        self,
        customer_id: str,
        campaign_id: str,
        primary_channel: str,
        content_id: str,
        user: Dict[str, Any],
        now: datetime,
        variant: str,
    ) -> DeliveryRecord:
        order = [primary_channel] + [c for c in _FALLBACK_ORDER if c != primary_channel]
        tried: List[str] = []
        for ch in order:
            adapter = self.adapters.get(ch)
            if adapter is None:
                continue
            tried.append(ch)
            if adapter.deliver(customer_id, content_id, user):
                return self._record(customer_id, campaign_id, ch, content_id, now,
                                    DeliveryStatus.SENT, variant,
                                    meta={"tried": tried, "primary": primary_channel})
        return self._record(customer_id, campaign_id, primary_channel, content_id, now,
                            DeliveryStatus.FAILED, variant,
                            meta={"reason": "all_channels_failed", "tried": tried})

    def _record(self, customer_id, campaign_id, channel, content_id, ts, status,
                variant, *, meta) -> DeliveryRecord:
        rec = DeliveryRecord(
            customer_id=customer_id,
            campaign_id=campaign_id,
            channel=channel,
            content_id=content_id,
            ts=ts,
            status=status,
            variant=variant,
            meta=meta,
        )
        self.log.append(rec)
        return rec
