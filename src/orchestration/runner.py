"""CampaignRunner — orchestrates one campaign run end-to-end (M3).

Pipeline (step ② of the MoEngage-style flow, after M2 segmentation):

    1. resolve audience    via CohortEngine.evaluate(campaign.audience_spec)
    2. (triggered)         keep only users who fired the trigger event
    3. frequency cap       FrequencyCapper -> capped users get CAPPED records
    4. allocate            control hold-out + A/B/n variant split (deterministic)
    5. control             -> HELDOUT_CONTROL records (no send)
    6. variants            -> gateway.send_batch(...) per variant

Audience accounting always balances, even when the gateway suppresses or fails
some sends (opt-out / unreachable / rate-limited)::

    len(audience) == sent + not_sent + control + capped   (+ triggered-excluded)

The runner depends only on the shared ``MessagingGateway`` protocol, so it
works with the real M1 ``Gateway`` or a test FakeGateway interchangeably.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from growth_common import DeliveryRecord, DeliveryStatus, MessagingGateway

from .allocator import CONTROL, allocate
from .frequency import FrequencyCapper
from .models import Campaign


@dataclass
class RunResult:
    """Summary of a single campaign run + every per-user DeliveryRecord."""
    campaign_id: str
    audience_size: int
    eligible_size: int                      # audience after trigger filtering
    sent_by_variant: Dict[str, int] = field(default_factory=dict)
    control_count: int = 0
    capped_count: int = 0
    not_sent_count: int = 0                 # variant-allocated but gateway suppressed/failed
    excluded_no_trigger: int = 0            # triggered campaigns only
    records: List[DeliveryRecord] = field(default_factory=list)

    @property
    def sent_count(self) -> int:
        return sum(self.sent_by_variant.values())

    @property
    def balances(self) -> bool:
        """Accounting identity: every eligible user lands in exactly one bucket."""
        return (
            self.sent_count + self.not_sent_count + self.control_count + self.capped_count
            == self.audience_size - self.excluded_no_trigger
        )


class CampaignRunner:
    def __init__(self, engine: Any, gateway: MessagingGateway):
        self.engine = engine
        self.gateway = gateway

    def run(
        self,
        campaign: Campaign,
        dataset: Dict[str, Any],
        now: datetime,
        history: Optional[List[DeliveryRecord]] = None,
        *,
        daily_cap: int = 1,
        triggered_users: Optional[Set[str]] = None,
    ) -> RunResult:
        """Execute ``campaign`` against ``dataset`` at time ``now``.

        ``triggered_users`` is the set of users who fired the schedule's
        trigger event (required for ``triggered`` campaigns; ignored for
        ``batch``). ``history`` is prior DeliveryRecords for frequency capping.
        """
        history = list(history or [])

        # 1. resolve audience from the cohort rule DSL
        audience = self.engine.evaluate(campaign.audience_spec, dataset=dataset, now=now)
        audience = set(audience)

        result = RunResult(
            campaign_id=campaign.id,
            audience_size=len(audience),
            eligible_size=len(audience),
        )

        # 2. triggered: only users who fired the trigger event are eligible
        if campaign.schedule.is_triggered:
            fired = triggered_users or set()
            eligible = audience & set(fired)
            result.excluded_no_trigger = len(audience) - len(eligible)
        else:
            eligible = audience
        result.eligible_size = len(eligible)

        # deterministic ordering for stable records/sends
        ordered = sorted(eligible)

        # 3. frequency cap + cross-campaign dedup
        capper = FrequencyCapper(daily_cap=daily_cap)
        cap = capper.filter(ordered, history, now, campaign_id=campaign.id)
        for cid, reason in cap.capped.items():
            result.records.append(
                DeliveryRecord(
                    customer_id=cid,
                    campaign_id=campaign.id,
                    channel=campaign.channel,
                    content_id="",
                    ts=now,
                    status=DeliveryStatus.CAPPED,
                    variant="capped",
                    meta={"reason": reason},
                )
            )
        result.capped_count = len(cap.capped)

        # 4. allocate the survivors into control / variants
        buckets = allocate(campaign, cap.allowed)

        control_ids: List[str] = []
        per_variant: Dict[str, List[str]] = {v.name: [] for v in campaign.variants}
        for cid in cap.allowed:  # preserve sorted order
            b = buckets[cid]
            if b == CONTROL:
                control_ids.append(cid)
            else:
                per_variant[b].append(cid)

        # 5. control hold-out -> HELDOUT_CONTROL, no send
        for cid in control_ids:
            result.records.append(
                DeliveryRecord(
                    customer_id=cid,
                    campaign_id=campaign.id,
                    channel=campaign.channel,
                    content_id="",
                    ts=now,
                    status=DeliveryStatus.HELDOUT_CONTROL,
                    variant=CONTROL,
                )
            )
        result.control_count = len(control_ids)

        # 6. each variant's users -> gateway.send_batch
        content_by_variant = {v.name: v.content_id for v in campaign.variants}
        for variant in campaign.variants:
            ids = per_variant[variant.name]
            if not ids:
                result.sent_by_variant[variant.name] = 0
                continue
            recs = self.gateway.send_batch(
                ids,
                campaign.channel,
                content_by_variant[variant.name],
                campaign_id=campaign.id,
                dataset=dataset,
                now=now,
                variant=variant.name,
            )
            result.records.extend(recs)
            sent = sum(1 for r in recs if r.status == DeliveryStatus.SENT)
            result.sent_by_variant[variant.name] = sent
            # gateway may suppress/fail some (opt-out / unreachable / rate-limited)
            result.not_sent_count += len(recs) - sent

        return result


__all__ = ["CampaignRunner", "RunResult"]
