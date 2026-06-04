"""End-to-end integration demo: the full Botim Growth pipeline in one run.

    M2 segment  ->  M3 orchestrate (A/B + control + freq-cap)  ->  M1 deliver
    M5 personalize (home-card payload)   |   M7 shadow-validate (gate)
    M4 funnel + attribution + cross-product funnel

Run:  python examples/e2e_demo.py
The same `build_world()` / `run_pipeline()` are exercised by
tests/test_integration_e2e.py, so this file is the single source of truth.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analytics import attribute, compute_funnel, cross_product_funnel
from cohort_engine import CohortEngine
from cohort_engine import templates as T
from growth_common import Channel, DeliveryRecord, DeliveryStatus
from messaging import Gateway
from orchestration import Campaign, CampaignRunner, Schedule, Variant
from personalization import Experience, ExperienceService, ExperienceStore, Variation
from shadow import compare, reconcile, split

NOW = datetime(2026, 6, 2, 12, 0, 0)
OPT_OUT = {"w2"}


# --------------------------------------------------------------------------- #
# 1. the world: users carry BOTH cohort attributes AND messaging fields
# --------------------------------------------------------------------------- #
def build_world() -> Dict[str, Any]:
    recent = NOW - timedelta(days=1)

    def u(cid, kyc, bal, wallet, country, token, uninstalled=False):
        return {"customer_id": cid, "is_kyc": kyc, "balance": bal,
                "wallet_activated": wallet, "country": country,
                "push_token": token, "phone": "+9715" + cid[-1],
                "last_active": recent, "app_uninstalled": uninstalled}

    users = [
        u("w1", True, 5000, False, "AE", "t1"),                 # cohort, healthy -> SENT
        u("w2", True, 3000, False, "AE", "t2"),                 # cohort, opted-out
        u("w3", True, 2000, False, "IN", "t3", uninstalled=True),  # cohort, unreachable
        u("w4", True, 1500, False, "AE", None),                 # cohort, no push_token -> unreachable (push)
        u("w5", True, 1200, False, "PH", "t5"),                 # cohort, healthy -> SENT
        u("w6", True, 200, True, "AE", "t6"),                   # not cohort (low bal, wallet on)
        u("w7", False, 0, False, "PH", "t7"),                   # not cohort (no kyc)
        u("w8", True, 8000, True, "AE", "t8"),                  # not cohort (wallet on)
    ]

    def ev(cid, name, ts, **kw):
        return {"customer_id": cid, "event_name": name, "ts": ts, **kw}

    j1 = datetime(2026, 6, 1)
    events = [
        # Call Made (cross-product step 1)
        ev("w1", "Call Made", datetime(2026, 5, 25)),
        ev("w5", "Call Made", datetime(2026, 5, 28)),
        ev("w4", "Call Made", datetime(2026, 5, 30)),
        ev("w8", "Call Made", datetime(2026, 5, 26)),
        # App Opened (funnel step 1)
        ev("w1", "App Opened", j1.replace(hour=10)),
        ev("w5", "App Opened", j1.replace(hour=9)),
        ev("w4", "App Opened", j1.replace(hour=8)),
        ev("w6", "App Opened", j1.replace(hour=7)),
        ev("w8", "App Opened", j1.replace(hour=6)),
        # Transfer (conversion; some AFTER the campaign send at NOW)
        ev("w1", "Transfer", NOW + timedelta(hours=6), converted=True),
        ev("w5", "Transfer", NOW + timedelta(hours=20), converted=True),
        ev("w8", "Transfer", j1.replace(hour=20)),  # pre-send, w8 not targeted
    ]
    return {"users": users, "events": events}


# --------------------------------------------------------------------------- #
# helper: a sizeable, deterministic 2-arm dataset for the shadow gate verdict
# --------------------------------------------------------------------------- #
def _arm(prefix: str, sent: int, conversions: int) -> List[DeliveryRecord]:
    recs = []
    for i in range(sent):
        recs.append(DeliveryRecord(
            customer_id=f"{prefix}{i}", campaign_id="shadow_exp", channel=Channel.PUSH,
            content_id="c", ts=NOW, status=DeliveryStatus.SENT, converted=(i < conversions)))
    return recs


# --------------------------------------------------------------------------- #
# the pipeline
# --------------------------------------------------------------------------- #
def run_pipeline(world: Dict[str, Any], now: datetime = NOW) -> Dict[str, Any]:
    engine = CohortEngine(world, now=now)
    cohort_spec = T.high_value_wallet_inactive(min_balance=1000)

    # --- M2: segment ---------------------------------------------------------
    audience = engine.evaluate(cohort_spec)

    # --- M3 + M1: orchestrate an A/B push campaign and deliver --------------
    campaign = Campaign(
        id="reactivation_push",
        audience_spec=cohort_spec,
        channel=Channel.PUSH,
        variants=[Variant("A", 1, "push_copy_A"), Variant("B", 1, "push_copy_B")],
        schedule=Schedule(start=now, end=now + timedelta(days=1), trigger_type="batch"),
        control_pct=0.0,
    )
    gateway = Gateway(opt_out=OPT_OUT)
    runner = CampaignRunner(engine, gateway)
    run_result = runner.run(campaign, world, now, daily_cap=99)

    # --- M5: personalize a home-screen card (gating demonstrated) -----------
    store = ExperienceStore()
    exp = Experience(
        key="home_card",
        audience_spec=cohort_spec,
        variations=[
            Variation("A", 1, {"default": {"title": "Activate your wallet"},
                                "ar": {"title": "فعّل محفظتك"}}),
            Variation("B", 1, {"default": {"title": "Unlock instant transfers"},
                                "ar": {"title": "حوالات فورية"}}),
        ],
        control_pct=0.0,
    )
    store.register(exp)
    svc = ExperienceService(engine, store)
    before_publish = svc.fetch({"customer_id": "w1"}, ["home_card"], world, now, locale="ar")
    store.publish("home_card")
    personalization = {
        cid: svc.fetch({"customer_id": cid}, ["home_card"], world, now, locale="ar")["home_card"]
        for cid in ["w1", "w5", "w6"]  # w6 not in audience -> None
    }

    # --- M7: shadow validation (5% split + dedup) + acceptance verdict ------
    arms = split(sorted(audience), shadow_pct=0.5)
    shadow_targets = [c for c, a in arms.items() if a == "shadow"]
    control_targets = [c for c, a in arms.items() if a == "control"]
    shadow_send, control_send, blocked = reconcile(shadow_targets, control_targets)
    # verdict needs volume -> deterministic synthetic arms (control 20.0%, shadow 18.8%);
    # at n=20000 a 1.2pp shortfall sits within a 2pp margin -> "not_worse" (gate passes)
    shadow_report = compare(_arm("c", 20000, 4000), _arm("s", 20000, 3760),
                            non_inferiority_margin=0.02)

    # --- M4: funnel + attribution + cross-product funnel --------------------
    funnel = compute_funnel(world["events"], ["App Opened", "Transfer"],
                            now=now, within_days=30)
    cross = cross_product_funnel(world["events"], ["Call Made", "App Opened", "Transfer"],
                                 now=now, within_days=30)
    conversions = [e for e in world["events"] if e["event_name"] == "Transfer" and e.get("converted")]
    attribution = attribute(run_result.records, conversions, window_hours=48)

    return {
        "audience": set(audience),
        "run_result": run_result,
        "delivery_records": run_result.records,
        "personalization_before_publish": before_publish,
        "personalization": personalization,
        "shadow_arms": arms,
        "shadow_send": shadow_send,
        "control_send": control_send,
        "shadow_blocked": blocked,
        "shadow_report": shadow_report,
        "funnel": funnel,
        "cross_product": cross,
        "attribution": attribution,
    }


def main() -> None:
    world = build_world()
    r = run_pipeline(world)
    line = "=" * 72
    print(line + f"\nBotim Growth — end-to-end pipeline @ {NOW.isoformat()}\n" + line)

    print(f"\n[M2] cohort audience ({len(r['audience'])}): {sorted(r['audience'])}")

    rr = r["run_result"]
    print(f"\n[M3+M1] campaign '{rr.campaign_id}': sent={rr.sent_count} "
          f"control={rr.control_count} capped={rr.capped_count} not_sent={rr.not_sent_count} "
          f"(balances={rr.balances})")
    for rec in r["delivery_records"]:
        print(f"    {rec.customer_id:>3}  {rec.status:<24} via {rec.channel:<6} variant={rec.variant}")

    print("\n[M5] personalization (home_card, locale=ar):")
    print(f"    before publish (gating): {r['personalization_before_publish']}")
    for cid, pl in r["personalization"].items():
        print(f"    {cid}: {pl}")

    rep = r["shadow_report"]
    print(f"\n[M7] shadow split: shadow={r['shadow_send']} control={r['control_send']} "
          f"blocked={r['shadow_blocked']}")
    print(f"    gate verdict: {rep.verdict}  (control={rep.control_rate:.3f} "
          f"shadow={rep.shadow_rate:.3f} ci=[{rep.diff_ci_low:.4f},{rep.diff_ci_high:.4f}] "
          f"margin={rep.non_inferiority_margin})")

    f, c = r["funnel"], r["cross_product"]
    print(f"\n[M4] funnel {f.steps}: counts={f.step_counts} overall={f.overall_conversion:.2f}")
    print(f"    cross-product {c.steps}: counts={c.step_counts} overall={c.overall_conversion:.2f}")
    at = r["attribution"]
    print(f"    attribution (48h, last_touch): conv/campaign={at.conversions_per_campaign} "
          f"rate={ {k: round(v,3) for k,v in at.conversion_rate_per_campaign.items()} } "
          f"unattributed={at.unattributed}")


if __name__ == "__main__":
    main()
