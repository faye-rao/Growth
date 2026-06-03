"""M3 Content & Push Orchestration — tests (TDD).

Covers deterministic variant split + control hold-out, frequency cap /
cross-campaign dedup, batch vs. triggered targeting, and an end-to-end run
that resolves a cohort DSL audience and sends via a FakeGateway.

The FakeGateway implements the shared ``growth_common.MessagingGateway``
protocol so these tests do NOT depend on the M1 messaging module.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from cohort_engine import CohortEngine
from cohort_engine.sample_data import NOW, build_sample_dataset
from growth_common import (
    DeliveryRecord,
    DeliveryStatus,
    MessagingGateway,
    stable_fraction,
)
from orchestration import (
    CONTROL,
    Campaign,
    CampaignRunner,
    FrequencyCapper,
    Schedule,
    Variant,
    allocate,
)


# --- FakeGateway: records every send as a SENT DeliveryRecord ----------------
class FakeGateway:
    """Minimal MessagingGateway: every targeted user gets a SENT record."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

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
        self.calls.append(
            {"ids": list(customer_ids), "channel": channel,
             "content_id": content_id, "variant": variant}
        )
        return [
            DeliveryRecord(
                customer_id=cid,
                campaign_id=campaign_id,
                channel=channel,
                content_id=content_id,
                ts=now,
                status=DeliveryStatus.SENT,
                variant=variant,
            )
            for cid in customer_ids
        ]


def test_fakegateway_satisfies_protocol():
    assert isinstance(FakeGateway(), MessagingGateway)


# --- fixtures ----------------------------------------------------------------
@pytest.fixture
def dataset():
    return build_sample_dataset()


@pytest.fixture
def now():
    return NOW


@pytest.fixture
def engine(dataset, now):
    return CohortEngine(dataset, now=now)


def _batch_schedule():
    return Schedule(start=NOW, end=NOW + timedelta(days=1), trigger_type="batch")


def _campaign(cid="c1", control_pct=0.0, variants=None, audience_spec=None,
              schedule=None, channel="push"):
    return Campaign(
        id=cid,
        audience_spec=audience_spec or {"match": {"type": "attribute",
                                                   "field": "is_kyc",
                                                   "operator": "eq", "value": True}},
        channel=channel,
        variants=variants or [Variant("A", 1, "ca"), Variant("B", 1, "cb")],
        control_pct=control_pct,
        schedule=schedule or _batch_schedule(),
    )


SYNTHETIC = [f"user{i}" for i in range(5000)]


# --- allocation: determinism + proportionality ------------------------------
def test_allocation_is_deterministic():
    c = _campaign(variants=[Variant("A", 1, "ca"), Variant("B", 1, "cb")])
    a1 = allocate(c, SYNTHETIC)
    a2 = allocate(c, list(reversed(SYNTHETIC)))
    assert a1 == a2  # order-independent, stable


def test_variant_split_roughly_proportional():
    c = _campaign(variants=[Variant("A", 3, "ca"), Variant("B", 1, "cb")])
    alloc = allocate(c, SYNTHETIC)
    a = sum(1 for v in alloc.values() if v == "A")
    b = sum(1 for v in alloc.values() if v == "B")
    assert a + b == len(SYNTHETIC)
    # 3:1 split -> A ~75%, tolerance for hashing noise
    assert 0.70 <= a / len(SYNTHETIC) <= 0.80
    assert 0.20 <= b / len(SYNTHETIC) <= 0.30


def test_control_holdout_fraction_and_stability():
    c = _campaign(control_pct=0.2,
                  variants=[Variant("A", 1, "ca"), Variant("B", 1, "cb")])
    alloc = allocate(c, SYNTHETIC)
    control = sum(1 for v in alloc.values() if v == CONTROL)
    assert 0.17 <= control / len(SYNTHETIC) <= 0.23  # ~20%
    # stable across re-allocation
    assert allocate(c, SYNTHETIC) == alloc
    # control membership matches stable_fraction directly
    for cid, bucket in alloc.items():
        if stable_fraction(c.id, cid) < 0.2:
            assert bucket == CONTROL
        else:
            assert bucket != CONTROL


def test_control_split_remaining_roughly_proportional():
    c = _campaign(control_pct=0.2,
                  variants=[Variant("A", 1, "ca"), Variant("B", 1, "cb")])
    alloc = allocate(c, SYNTHETIC)
    a = sum(1 for v in alloc.values() if v == "A")
    b = sum(1 for v in alloc.values() if v == "B")
    # of the ~80% non-control, A and B should be roughly equal
    assert abs(a - b) / len(SYNTHETIC) < 0.05


# --- frequency cap + cross-campaign dedup ------------------------------------
def test_daily_cap_blocks_users_over_cap():
    capper = FrequencyCapper(daily_cap=1)
    hist = [
        DeliveryRecord("u1", "other", "push", "x", NOW, DeliveryStatus.SENT),
    ]
    res = capper.filter(["u1", "u2"], hist, NOW, campaign_id="c1")
    assert res.allowed == ["u2"]
    assert "u1" in res.capped
    assert res.capped["u1"] == "daily_cap_reached"


def test_daily_cap_counts_only_sent_today():
    capper = FrequencyCapper(daily_cap=1)
    hist = [
        # yesterday -> does not count
        DeliveryRecord("u1", "other", "push", "x", NOW - timedelta(days=1),
                       DeliveryStatus.SENT),
        # capped status -> not a delivered touch
        DeliveryRecord("u2", "other", "push", "x", NOW, DeliveryStatus.CAPPED),
    ]
    res = capper.filter(["u1", "u2"], hist, NOW, campaign_id="c1")
    assert set(res.allowed) == {"u1", "u2"}
    assert res.capped == {}


def test_cross_campaign_dedup_blocks_already_touched():
    capper = FrequencyCapper(daily_cap=5)
    hist = [
        DeliveryRecord("u1", "c1", "push", "x", NOW, DeliveryStatus.SENT),
    ]
    res = capper.filter(["u1", "u2"], hist, NOW, campaign_id="c1")
    assert res.allowed == ["u2"]
    assert res.capped["u1"] == "already_touched_by_campaign_today"


# --- triggered vs batch targeting --------------------------------------------
def test_triggered_only_targets_users_with_event(engine, dataset, now):
    sched = Schedule(start=now, end=now + timedelta(days=1),
                     trigger_type="triggered", trigger_event="App Opened")
    c = _campaign(cid="ct", schedule=sched,
                  variants=[Variant("A", 1, "ca")], control_pct=0.0)
    gw = FakeGateway()
    runner = CampaignRunner(engine, gw)
    # audience = all KYC users {u1,u2,u4,u5}; trigger fired only by {u2,u5}
    res = runner.run(c, dataset, now, triggered_users={"u2", "u5"})
    sent_ids = {r.customer_id for r in res.records if r.is_sent}
    assert sent_ids == {"u2", "u5"}
    assert res.excluded_no_trigger == 2  # u1, u4 in audience but no trigger


def test_batch_targets_full_audience(engine, dataset, now):
    c = _campaign(cid="cb", variants=[Variant("A", 1, "ca")], control_pct=0.0)
    gw = FakeGateway()
    runner = CampaignRunner(engine, gw)
    res = runner.run(c, dataset, now)
    sent_ids = {r.customer_id for r in res.records if r.is_sent}
    assert sent_ids == {"u1", "u2", "u4", "u5"}  # all KYC users
    assert res.excluded_no_trigger == 0


# --- end-to-end: counts add up -----------------------------------------------
def test_end_to_end_counts_balance(engine, dataset, now):
    c = _campaign(cid="e2e", control_pct=0.25,
                  variants=[Variant("A", 1, "ca"), Variant("B", 1, "cb")])
    # pre-touch u1 today by another campaign -> should be capped (daily_cap=1)
    hist = [DeliveryRecord("u1", "other", "push", "x", now, DeliveryStatus.SENT)]
    gw = FakeGateway()
    runner = CampaignRunner(engine, gw)
    res = runner.run(c, dataset, now, history=hist, daily_cap=1)

    assert res.audience_size == 4  # u1,u2,u4,u5
    # accounting identity: audience == sent + not_sent + control + capped (batch -> no excluded)
    assert res.balances
    assert res.sent_count + res.not_sent_count + res.control_count + res.capped_count == res.audience_size
    assert res.capped_count == 1  # u1
    # every non-control survivor produced exactly one SENT record
    assert res.sent_count == sum(len(call["ids"]) for call in gw.calls)
    # records cover every audience member exactly once
    assert len({r.customer_id for r in res.records}) == res.audience_size


class MixedGateway:
    """Gateway that suppresses a fixed set of users and SENDS the rest (review regression).

    Exercises the path where variant-allocated users do NOT all become SENT, which
    must still keep the run-result accounting balanced.
    """

    def __init__(self, suppress=("u2",)):
        self.suppress = set(suppress)

    def send_batch(self, customer_ids, channel, content_id, *, campaign_id,
                   dataset, now, variant="default"):
        out = []
        for cid in sorted(customer_ids):
            status = (DeliveryStatus.SUPPRESSED_OPTOUT if cid in self.suppress
                      else DeliveryStatus.SENT)
            out.append(DeliveryRecord(cid, campaign_id, channel, content_id, now,
                                      status, variant=variant))
        return out


def test_accounting_balances_with_suppressing_gateway(engine, dataset, now):
    """audience == sent + not_sent + control + capped, even when sends are suppressed."""
    # control_pct=0 so all 4 KYC users go to a variant; u2 is always suppressed
    c = _campaign(cid="mixed", control_pct=0.0,
                  variants=[Variant("A", 1, "ca"), Variant("B", 1, "cb")])
    runner = CampaignRunner(engine, MixedGateway(suppress={"u2"}))
    res = runner.run(c, dataset, now, daily_cap=99)  # no capping

    assert res.not_sent_count >= 1            # u2 suppressed; the bug would have lost it
    assert res.sent_count >= 1                # others sent
    assert res.balances
    assert (res.sent_count + res.not_sent_count + res.control_count + res.capped_count
            == res.audience_size)
    # records still cover every audience member exactly once
    assert len({r.customer_id for r in res.records}) == res.audience_size


def test_end_to_end_send_uses_variant_content(engine, dataset, now):
    c = _campaign(cid="content", control_pct=0.0,
                  variants=[Variant("A", 1, "alpha"), Variant("B", 1, "beta")])
    gw = FakeGateway()
    runner = CampaignRunner(engine, gw)
    res = runner.run(c, dataset, now)
    by_variant = {r.variant: r.content_id for r in res.records if r.is_sent}
    if "A" in by_variant:
        assert by_variant["A"] == "alpha"
    if "B" in by_variant:
        assert by_variant["B"] == "beta"
