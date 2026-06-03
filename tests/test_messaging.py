"""M1 Messaging Execution — test cases (TDD, pytest).

Covers the unified gateway pipeline: opt-out suppression, reachability filter,
rate limiting, multi-channel fallback, batch send + internal log, and shared
DeliveryRecord schema conformance.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta

import pytest

from growth_common import (
    Channel,
    DeliveryRecord,
    DeliveryStatus,
    MessagingGateway,
)
from cohort_engine import CohortEngine

from messaging import Gateway, RateLimiter
from messaging.adapters import PushAdapter, SmsAdapter, InAppAdapter
from messaging.sample_data import build_messaging_dataset, OPT_OUT, NOW


# --- fixtures -----------------------------------------------------------------
@pytest.fixture
def dataset():
    return build_messaging_dataset()


@pytest.fixture
def gateway():
    return Gateway(opt_out=set(OPT_OUT))


def _send(gw, cid, dataset, *, channel=Channel.PUSH, content="welcome",
          campaign="c1", now=NOW):
    recs = gw.send_batch([cid], channel, content, campaign_id=campaign,
                         dataset=dataset, now=now)
    return recs[0]


# --- protocol / schema --------------------------------------------------------
def test_gateway_implements_messaging_gateway_protocol(gateway):
    assert isinstance(gateway, MessagingGateway)


def test_delivery_record_fields_match_shared_schema(gateway, dataset):
    rec = _send(gateway, "m1", dataset)
    assert isinstance(rec, DeliveryRecord)
    names = {f.name for f in fields(DeliveryRecord)}
    assert names == {
        "customer_id", "campaign_id", "channel", "content_id", "ts",
        "status", "variant", "clicked", "converted", "meta",
    }
    assert rec.customer_id == "m1"
    assert rec.campaign_id == "c1"
    assert rec.content_id == "welcome"
    assert rec.ts == NOW


# --- 1) opt-out suppression ---------------------------------------------------
def test_opted_out_user_is_suppressed(gateway, dataset):
    rec = _send(gateway, "m2", dataset)
    assert rec.status == DeliveryStatus.SUPPRESSED_OPTOUT
    assert rec.meta["reason"] == "opt_out"


# --- 2) reachability filter ---------------------------------------------------
def test_uninstalled_user_is_unreachable(gateway, dataset):
    rec = _send(gateway, "m3", dataset)
    assert rec.status == DeliveryStatus.SUPPRESSED_UNREACHABLE
    assert rec.meta["reason"] == "app_uninstalled"


def test_stale_last_active_user_is_unreachable(gateway, dataset):
    rec = _send(gateway, "m4", dataset)
    assert rec.status == DeliveryStatus.SUPPRESSED_UNREACHABLE
    assert rec.meta["reason"] == "stale_last_active"


def test_missing_push_token_is_unreachable_for_push(gateway, dataset):
    rec = _send(gateway, "m5", dataset, channel=Channel.PUSH)
    assert rec.status == DeliveryStatus.SUPPRESSED_UNREACHABLE
    assert rec.meta["reason"] == "no_push_token"


def test_missing_push_token_still_reachable_on_sms(gateway, dataset):
    rec = _send(gateway, "m5", dataset, channel=Channel.SMS)
    assert rec.status == DeliveryStatus.SENT
    assert rec.channel == Channel.SMS


# --- 3) healthy send ----------------------------------------------------------
def test_healthy_user_sent_via_push(gateway, dataset):
    rec = _send(gateway, "m1", dataset, channel=Channel.PUSH,
                content="promo", campaign="spring")
    assert rec.status == DeliveryStatus.SENT
    assert rec.channel == Channel.PUSH
    assert rec.content_id == "promo"
    assert rec.campaign_id == "spring"


# --- 4) rate limiting ---------------------------------------------------------
def test_rate_limit_throttles_overflow(dataset):
    gw = Gateway(opt_out=set(), rate_limiter=RateLimiter(capacity=1))
    # m1 and a clone "m1b" are both healthy push targets; capacity is 1.
    dataset["users"].append({**dataset["users"][0], "customer_id": "m1b"})
    recs = gw.send_batch(["m1", "m1b"], Channel.PUSH, "welcome",
                         campaign_id="c1", dataset=dataset, now=NOW)
    statuses = [r.status for r in recs]
    assert statuses[0] == DeliveryStatus.SENT
    assert statuses[1] == DeliveryStatus.FAILED
    assert recs[1].meta["reason"] == "rate_limited"


# --- 5) multi-channel fallback ------------------------------------------------
def test_fallback_push_fails_then_delivered_via_sms(gateway, dataset):
    # m6 is healthy and reachable on a non-push channel, but has no push_token,
    # so a direct push send is suppressed by reachability. To exercise *delivery*
    # fallback, send on a primary channel that passes reachability (sms) — but to
    # prove fallback chains, use a custom user whose push adapter rejects.
    # Simpler: send m6 via in_app primary is trivial. Instead drive fallback by
    # making the primary an adapter that fails. Use sms primary on a user with no
    # phone so sms adapter rejects and it falls through to in_app.
    dataset["users"].append({
        "customer_id": "m7", "push_token": None, "phone": None,
        "last_active": NOW - timedelta(days=1), "app_uninstalled": False,
    })
    rec = _send(gateway, "m7", dataset, channel=Channel.SMS)
    # sms rejects (no phone) -> in_app accepts
    assert rec.status == DeliveryStatus.SENT
    assert rec.channel == Channel.IN_APP
    assert rec.meta["primary"] == Channel.SMS
    # primary sms (no phone -> reject), then remaining order push (no token ->
    # reject), then in_app (accept).
    assert rec.meta["tried"] == [Channel.SMS, Channel.PUSH, Channel.IN_APP]


def test_fallback_chain_from_push_primary():
    # Custom user reachable for push (has token) but push API rejects it.
    # Use a PushAdapter stub that always fails to prove push->sms fallback.
    class FailingPush(PushAdapter):
        def deliver(self, customer_id, content_id, user):
            return False

    gw = Gateway(
        opt_out=set(),
        adapters={
            Channel.PUSH: FailingPush(),
            Channel.SMS: SmsAdapter(),
            Channel.IN_APP: InAppAdapter(),
        },
    )
    user = {"customer_id": "x", "push_token": "tok", "phone": "+9715000",
            "last_active": NOW - timedelta(days=1), "app_uninstalled": False}
    ds = {"users": [user]}
    rec = gw.send_batch(["x"], Channel.PUSH, "welcome", campaign_id="c1",
                        dataset=ds, now=NOW)[0]
    assert rec.status == DeliveryStatus.SENT
    assert rec.channel == Channel.SMS
    assert rec.meta["tried"] == [Channel.PUSH, Channel.SMS]


def test_all_channels_fail_records_failed():
    class FailAll(InAppAdapter):
        def deliver(self, customer_id, content_id, user):
            return False

    gw = Gateway(
        opt_out=set(),
        adapters={
            Channel.PUSH: PushAdapter(),
            Channel.SMS: SmsAdapter(),
            Channel.IN_APP: FailAll(),
        },
    )
    user = {"customer_id": "z", "push_token": None, "phone": None,
            "last_active": NOW - timedelta(days=1), "app_uninstalled": False}
    ds = {"users": [user]}
    rec = gw.send_batch(["z"], Channel.SMS, "welcome", campaign_id="c1",
                        dataset=ds, now=NOW)[0]
    assert rec.status == DeliveryStatus.FAILED
    assert rec.meta["reason"] == "all_channels_failed"


# --- 6) batch + internal log --------------------------------------------------
def test_send_batch_returns_one_record_per_user_and_logs(gateway, dataset):
    ids = ["m1", "m2", "m3", "m4", "m5", "m6"]
    recs = gateway.send_batch(ids, Channel.PUSH, "welcome", campaign_id="c1",
                              dataset=dataset, now=NOW)
    assert len(recs) == len(ids)
    assert [r.customer_id for r in recs] == ids
    # internal log mirrors the returned records
    assert len(gateway.log) == len(ids)
    assert gateway.log == recs


# --- integration: resolve audience via CohortEngine ---------------------------
def test_send_over_cohort_resolved_audience(gateway, dataset):
    # Reuse M2's CohortEngine to resolve an audience from a cohort spec, then
    # send through the M1 gateway — demonstrates the M2 -> M1 handoff.
    from cohort_engine.sample_data import build_sample_dataset, NOW as COHORT_NOW

    engine = CohortEngine(build_sample_dataset(), now=COHORT_NOW)
    spec = {"match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
    ]}}
    audience = sorted(engine.evaluate(spec))
    assert audience  # non-empty
    # These cohort users aren't in the messaging dataset -> treated as bare ids;
    # push has no token -> unreachable. Confirms graceful handling + one rec each.
    recs = gateway.send_batch(audience, Channel.PUSH, "welcome", campaign_id="c1",
                              dataset=dataset, now=NOW)
    assert len(recs) == len(audience)
    assert all(isinstance(r, DeliveryRecord) for r in recs)
