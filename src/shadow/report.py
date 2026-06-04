"""A/B comparison report for the shadow-validation acceptance gate.

Goal: prove the new system (``shadow`` arm) is **not significantly worse** than
MoEngage (``control`` arm) on the conversion metric, so it can replace MoEngage.

Pipeline::

    arm_metrics(records)              -> {sent, conversions, conversion_rate}
    two_proportion_ztest(c1,n1,c2,n2) -> (z, p_two_sided)   # normal approx, stdlib math
    compare(control, shadow, margin)  -> ShadowReport(..., verdict)

The verdict is a **non-inferiority** decision: shadow is acceptable ("not_worse")
unless it is *significantly* below control by more than ``non_inferiority_margin``.
Zero third-party deps — significance uses the normal CDF via ``math.erf``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from growth_common import DeliveryRecord

SIGNIFICANCE_ALPHA = 0.05
Z_CRIT_95 = 1.959963985  # two-sided 95% normal critical value


# --- per-arm metrics ----------------------------------------------------------
def arm_metrics(records: List[DeliveryRecord]) -> Dict[str, float]:
    """Conversion metrics over the **sent** records of one arm.

    ``sent`` counts records with ``status == SENT``; ``conversions`` counts those
    that also have ``converted=True``; ``conversion_rate = conversions / sent``
    with a guard so no sent -> rate ``0.0`` (no ZeroDivisionError).
    """
    sent = sum(1 for r in records if r.is_sent)
    conversions = sum(1 for r in records if r.is_sent and r.converted)
    rate = conversions / sent if sent else 0.0
    return {"sent": sent, "conversions": conversions, "conversion_rate": rate}


# --- significance test --------------------------------------------------------
def _normal_cdf(x: float) -> float:
    """Standard normal CDF Φ(x) via the error function (stdlib ``math``)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_proportion_ztest(c1: int, n1: int, c2: int, n2: int) -> Tuple[float, float]:
    """Pooled two-proportion z-test (normal approximation).

    Tests H0: p1 == p2 where p1 = c1/n1 (e.g. control) and p2 = c2/n2 (shadow).
    Returns ``(z, p_two_sided)``. ``z`` carries the sign of ``p1 - p2`` (positive
    when arm 1 converts higher). Degenerate inputs (no samples, or zero pooled
    variance) yield ``(0.0, 1.0)`` — no evidence of a difference.
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0, 1.0
    p1 = c1 / n1
    p2 = c2 / n2
    pooled = (c1 + c2) / (n1 + n2)
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / n1 + 1.0 / n2))
    if se == 0.0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p_two_sided = 2.0 * (1.0 - _normal_cdf(abs(z)))
    return z, p_two_sided


def _unpooled_se(rate_c: float, n_c: int, rate_s: float, n_s: int) -> float:
    """Unpooled standard error of (shadow_rate - control_rate).

    Unpooled (not assuming equal proportions) is the correct SE for a
    margin-shifted non-inferiority comparison.
    """
    if n_c <= 0 or n_s <= 0:
        return 0.0
    return math.sqrt(rate_c * (1.0 - rate_c) / n_c + rate_s * (1.0 - rate_s) / n_s)


# --- report -------------------------------------------------------------------
@dataclass
class ShadowReport:
    """Acceptance-gate comparison of control (MoEngage) vs. shadow (new system)."""

    control_sent: int
    control_conversions: int
    control_rate: float
    shadow_sent: int
    shadow_conversions: int
    shadow_rate: float
    absolute_lift: float          # shadow_rate - control_rate
    relative_lift: float          # absolute_lift / control_rate (0 if control_rate == 0)
    z: float
    p_value: float
    significant: bool             # p_value < SIGNIFICANCE_ALPHA
    non_inferiority_margin: float
    verdict: str                  # shadow_better | not_worse | worse | inconclusive
    diff_ci_low: float = 0.0      # 95% CI lower bound on (shadow_rate - control_rate)
    diff_ci_high: float = 0.0     # 95% CI upper bound


def compare(
    control_records: List[DeliveryRecord],
    shadow_records: List[DeliveryRecord],
    *,
    non_inferiority_margin: float = 0.0,
) -> ShadowReport:
    """Compare the two arms and decide whether shadow may replace MoEngage.

    Verdict logic — a proper **non-inferiority** decision based on the 95%
    confidence interval ``[lo, hi]`` of the difference ``d = shadow_rate -
    control_rate`` (unpooled SE):

    * ``shadow_better`` — ``lo > 0`` (whole CI above zero: significantly better).
    * ``not_worse`` — ``lo >= -margin`` (worst plausible case is within the
      tolerance; the new system passes the gate — including a near-identical
      large sample even if the equality test is not "significant").
    * ``worse`` — ``hi < -margin`` (whole CI below the margin: significantly worse).
    * ``inconclusive`` — CI straddles ``-margin`` (underpowered / degenerate).

    The ``z``/``p_value``/``significant`` fields report the pooled two-proportion
    equality test for transparency, but do not drive the gate decision.
    """
    cm = arm_metrics(control_records)
    sm = arm_metrics(shadow_records)
    control_rate = cm["conversion_rate"]
    shadow_rate = sm["conversion_rate"]

    absolute_lift = shadow_rate - control_rate
    relative_lift = absolute_lift / control_rate if control_rate else 0.0

    z, p_value = two_proportion_ztest(
        cm["conversions"], cm["sent"], sm["conversions"], sm["sent"]
    )
    significant = p_value < SIGNIFICANCE_ALPHA

    se = _unpooled_se(control_rate, cm["sent"], shadow_rate, sm["sent"])
    if cm["sent"] == 0 or sm["sent"] == 0 or se == 0.0:
        ci_low = ci_high = absolute_lift
        verdict = "inconclusive"
    else:
        half = Z_CRIT_95 * se
        ci_low = absolute_lift - half
        ci_high = absolute_lift + half
        if ci_low > 0:
            verdict = "shadow_better"
        elif ci_low >= -non_inferiority_margin:
            verdict = "not_worse"
        elif ci_high < -non_inferiority_margin:
            verdict = "worse"
        else:
            verdict = "inconclusive"

    return ShadowReport(
        control_sent=cm["sent"],
        control_conversions=cm["conversions"],
        control_rate=control_rate,
        shadow_sent=sm["sent"],
        shadow_conversions=sm["conversions"],
        shadow_rate=shadow_rate,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        z=z,
        p_value=p_value,
        significant=significant,
        non_inferiority_margin=non_inferiority_margin,
        verdict=verdict,
        diff_ci_low=ci_low,
        diff_ci_high=ci_high,
    )


__all__ = [
    "arm_metrics",
    "two_proportion_ztest",
    "ShadowReport",
    "compare",
    "SIGNIFICANCE_ALPHA",
]
