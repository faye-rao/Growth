"""End-to-end integration test: segment -> orchestrate -> deliver ->
personalize -> shadow-validate -> funnel/attribution, asserting the modules
cohere (data flows correctly across M2/M3/M1/M5/M7/M4).

Exercises the exact `run_pipeline` used by examples/e2e_demo.py.
"""
import os
import sys

import pytest

# import the pipeline from examples/ (single source of truth)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import e2e_demo  # noqa: E402
from growth_common import DeliveryStatus  # noqa: E402


@pytest.fixture(scope="module")
def result():
    return e2e_demo.run_pipeline(e2e_demo.build_world())


# --- M2 -> M3 -> M1 ----------------------------------------------------------
def test_audience_is_the_high_value_cohort(result):
    assert result["audience"] == {"w1", "w2", "w3", "w4", "w5"}


def test_campaign_accounting_balances(result):
    rr = result["run_result"]
    assert rr.balances
    assert rr.sent_count + rr.not_sent_count + rr.control_count + rr.capped_count == rr.audience_size
    # records cover every audience member exactly once
    assert {r.customer_id for r in rr.records} == result["audience"]


def test_delivery_outcomes_match_reachability(result):
    by_id = {r.customer_id: r for r in result["delivery_records"]}
    assert by_id["w1"].status == DeliveryStatus.SENT               # healthy
    assert by_id["w5"].status == DeliveryStatus.SENT               # healthy
    assert by_id["w2"].status == DeliveryStatus.SUPPRESSED_OPTOUT  # opted out
    assert by_id["w3"].status == DeliveryStatus.SUPPRESSED_UNREACHABLE  # uninstalled
    assert by_id["w4"].status == DeliveryStatus.SUPPRESSED_UNREACHABLE  # no push_token


# --- M5 personalization ------------------------------------------------------
def test_personalization_gating_then_hit(result):
    # gating: before publish, even an audience member gets nothing
    assert result["personalization_before_publish"]["home_card"] is None
    # after publish: audience members get an (Arabic) payload; non-member gets None
    assert result["personalization"]["w1"] is not None
    assert "title" in result["personalization"]["w1"]
    assert result["personalization"]["w5"] is not None
    assert result["personalization"]["w6"] is None  # not in audience


# --- M7 shadow validation ----------------------------------------------------
def test_shadow_arms_are_disjoint_no_double_send(result):
    s, c = set(result["shadow_send"]), set(result["control_send"])
    assert s.isdisjoint(c)                                   # dedup: no double-send
    assert s | c == result["audience"]                       # everyone covered once


def test_shadow_gate_verdict_not_worse(result):
    rep = result["shadow_report"]
    assert rep.verdict == "not_worse"                        # passes acceptance gate
    assert rep.diff_ci_low >= -rep.non_inferiority_margin


# --- M4 funnel / attribution / cross-product ---------------------------------
def test_funnel_counts_and_rates(result):
    f = result["funnel"]
    assert f.step_counts == [5, 3]                           # App Opened -> Transfer
    assert f.overall_conversion == pytest.approx(0.6)
    assert 0.0 <= f.step_conversion[1] <= 1.0


def test_cross_product_funnel(result):
    c = result["cross_product"]
    assert c.steps == ["Call Made", "App Opened", "Transfer"]
    assert c.step_counts == [4, 4, 3]                        # the MoEngage-can't-do journey


def test_attribution_credits_campaign(result):
    at = result["attribution"]
    # both converters (w1, w5) were SENT by the campaign within the 48h window
    assert at.conversions_per_campaign.get("reactivation_push") == 2
    assert at.conversion_rate_per_campaign["reactivation_push"] == pytest.approx(1.0)
    assert at.unattributed == 0
