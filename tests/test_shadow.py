"""M7 Shadow Validation Framework — tests (TDD).

Covers the acceptance gate for replacing MoEngage:

* deterministic traffic split (~shadow_pct slice, stable per user),
* the dedup middle-layer (no user double-sent; arms reconcile to disjoint sends),
* the two-proportion z-test (asserted against a textbook value),
* per-arm conversion metrics incl. the no-sent /0 guard,
* the ``compare`` verdict matrix (better / worse / not_worse / inconclusive) and
  that the verdict honors ``non_inferiority_margin``.

Synthetic ``DeliveryRecord`` lists are built locally; no dependency on M1/M2/M3.
"""
from __future__ import annotations

from datetime import datetime

from growth_common import DeliveryRecord, DeliveryStatus, stable_fraction
from shadow import (
    DedupLedger,
    ShadowReport,
    arm_metrics,
    assign_arm,
    compare,
    reconcile,
    split,
    two_proportion_ztest,
)

NOW = datetime(2026, 6, 4, 12, 0, 0)
SYNTHETIC = [f"user{i}" for i in range(5000)]


# --- helpers -----------------------------------------------------------------
def _records(n_sent: int, n_conv: int, *, prefix: str, campaign: str = "shadow_run"):
    """Build ``n_sent`` SENT records, the first ``n_conv`` of which converted."""
    out = []
    for i in range(n_sent):
        out.append(
            DeliveryRecord(
                customer_id=f"{prefix}{i}",
                campaign_id=campaign,
                channel="push",
                content_id="msg",
                ts=NOW,
                status=DeliveryStatus.SENT,
                converted=i < n_conv,
            )
        )
    return out


# --- splitter: proportion + stability ----------------------------------------
def test_split_roughly_matches_shadow_pct():
    alloc = split(SYNTHETIC, 0.05)
    shadow = sum(1 for v in alloc.values() if v == "shadow")
    # ~5% slice, tolerance for hashing noise
    assert 0.03 <= shadow / len(SYNTHETIC) <= 0.07


def test_split_arm_values_are_shadow_or_control():
    alloc = split(SYNTHETIC, 0.05)
    assert set(alloc.values()) <= {"shadow", "control"}


def test_assign_arm_is_stable_across_calls():
    for cid in SYNTHETIC[:200]:
        a = assign_arm(cid, shadow_pct=0.05)
        b = assign_arm(cid, shadow_pct=0.05)
        assert a == b


def test_split_is_order_independent_and_deterministic():
    a1 = split(SYNTHETIC, 0.1)
    a2 = split(list(reversed(SYNTHETIC)), 0.1)
    assert a1 == a2


def test_assign_arm_matches_stable_fraction_boundary():
    for cid in SYNTHETIC[:200]:
        arm = assign_arm(cid, shadow_pct=0.05)
        if stable_fraction("shadow", cid) < 0.05:
            assert arm == "shadow"
        else:
            assert arm == "control"


def test_split_pct_zero_and_one():
    assert all(v == "control" for v in split(SYNTHETIC, 0.0).values())
    assert all(v == "shadow" for v in split(SYNTHETIC, 1.0).values())


# --- dedup middle-layer -------------------------------------------------------
def test_dedup_blocks_second_send_same_day():
    ledger = DedupLedger()
    assert ledger.allow("u1", "2026-06-04") is True
    assert ledger.allow("u1", "2026-06-04") is False  # already sent today


def test_dedup_allows_same_user_different_day():
    ledger = DedupLedger()
    assert ledger.allow("u1", "2026-06-04") is True
    assert ledger.allow("u1", "2026-06-05") is True


def test_reconcile_yields_disjoint_arms():
    # users in both target lists must not be sent by both systems
    shadow_targets = ["u1", "u2", "u3"]
    control_targets = ["u3", "u4", "u5"]  # u3 overlaps
    shadow_send, control_send, blocked = reconcile(shadow_targets, control_targets)
    assert set(shadow_send).isdisjoint(set(control_send))  # no user in both
    assert "u3" in shadow_send and "u3" not in control_send  # shadow wins the user
    assert "u3" in blocked
    assert set(shadow_send) | set(control_send) == {"u1", "u2", "u3", "u4", "u5"}


def test_reconcile_collapses_intra_arm_repeats():
    shadow_send, control_send, blocked = reconcile(["u1", "u1"], ["u2", "u2"])
    assert shadow_send == ["u1"]
    assert control_send == ["u2"]
    assert blocked == {"u1", "u2"}


# --- two-proportion z-test ----------------------------------------------------
def test_ztest_textbook_value():
    # 10/100 vs 20/100 -> z ~ -1.98, two-sided p ~ 0.0477 (classic example)
    z, p = two_proportion_ztest(10, 100, 20, 100)
    assert z == _approx(-1.9803, tol=1e-3)
    assert p == _approx(0.0477, tol=1e-3)


def test_ztest_equal_proportions_is_null():
    z, p = two_proportion_ztest(50, 1000, 50, 1000)
    assert z == 0.0
    assert p == 1.0


def test_ztest_zero_samples_guarded():
    assert two_proportion_ztest(0, 0, 5, 100) == (0.0, 1.0)


def _approx(value, tol=1e-9):
    class _A:
        def __eq__(self, other):
            return abs(other - value) <= tol
    return _A()


# --- arm metrics --------------------------------------------------------------
def test_arm_metrics_conversion_rate_math():
    m = arm_metrics(_records(200, 50, prefix="s"))
    assert m["sent"] == 200
    assert m["conversions"] == 50
    assert m["conversion_rate"] == _approx(0.25)


def test_arm_metrics_ignores_non_sent_and_unconverted():
    recs = _records(3, 1, prefix="s")
    # add a non-sent record that "converted" -> must not count
    recs.append(
        DeliveryRecord("x", "c", "push", "m", NOW,
                       DeliveryStatus.SUPPRESSED_OPTOUT, converted=True)
    )
    m = arm_metrics(recs)
    assert m["sent"] == 3
    assert m["conversions"] == 1


def test_arm_metrics_zero_sent_guard():
    m = arm_metrics([])
    assert m["sent"] == 0
    assert m["conversion_rate"] == 0.0  # no /0 error


# --- compare: verdict matrix --------------------------------------------------
def test_compare_shadow_clearly_better_is_significant():
    control = _records(1000, 100, prefix="c")   # 10%
    shadow = _records(1000, 200, prefix="s")    # 20%
    rep = compare(control, shadow)
    assert isinstance(rep, ShadowReport)
    assert rep.verdict == "shadow_better"
    assert rep.significant is True
    assert rep.absolute_lift == _approx(0.10)


def test_compare_shadow_clearly_worse_is_significant():
    control = _records(1000, 200, prefix="c")   # 20%
    shadow = _records(1000, 100, prefix="s")    # 10%
    rep = compare(control, shadow)
    assert rep.verdict == "worse"
    assert rep.significant is True


def test_compare_near_equal_large_sample_not_worse():
    # large sample, shadow marginally below control: a tiny but statistically
    # significant shortfall that a positive non-inferiority margin tolerates.
    control = _records(20000, 4000, prefix="c")  # 20.0%
    shadow = _records(20000, 3760, prefix="s")   # 18.8% -> significant shortfall
    rep = compare(control, shadow, non_inferiority_margin=0.02)
    assert rep.significant is True
    assert rep.verdict == "not_worse"  # shortfall 1.2pp <= margin 2pp


def test_compare_tiny_sample_inconclusive():
    control = _records(10, 5, prefix="c")   # 50%
    shadow = _records(10, 3, prefix="s")    # 30%
    rep = compare(control, shadow)
    assert rep.significant is False
    assert rep.verdict == "inconclusive"


def test_equivalent_large_sample_is_not_worse_even_if_not_significant():
    # Near-identical arms at large n: the equality test is NOT significant, but the
    # difference CI sits within the margin -> the gate should PASS (not_worse).
    # (The old significance-gated logic wrongly returned "inconclusive" here.)
    control = _records(10000, 2000, prefix="c")  # 20.0%
    shadow = _records(10000, 2000, prefix="s")   # 20.0%
    rep = compare(control, shadow, non_inferiority_margin=0.02)
    assert rep.significant is False
    assert rep.verdict == "not_worse"
    assert rep.diff_ci_low >= -0.02


def test_compare_zero_conversions_both_arms_inconclusive():
    control = _records(100, 0, prefix="c")
    shadow = _records(100, 0, prefix="s")
    rep = compare(control, shadow)
    assert rep.verdict == "inconclusive"  # zero variance -> cannot bound


def test_compare_empty_arm_inconclusive():
    rep = compare([], _records(100, 20, prefix="s"))
    assert rep.verdict == "inconclusive"


def test_verdict_honors_non_inferiority_margin():
    # same data, two margins -> "worse" with margin 0, "not_worse" with a margin
    # that covers the (significant) shortfall.
    control = _records(20000, 4000, prefix="c")  # 20.0%
    shadow = _records(20000, 3760, prefix="s")   # 18.8%, shortfall 1.2pp
    strict = compare(control, shadow, non_inferiority_margin=0.0)
    lenient = compare(control, shadow, non_inferiority_margin=0.02)
    assert strict.significant and lenient.significant
    assert strict.verdict == "worse"
    assert lenient.verdict == "not_worse"
