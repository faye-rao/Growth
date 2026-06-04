"""Botim Growth Platform — M7 Shadow Validation Framework (MVP).

The acceptance gate for replacing MoEngage. Run the new system on a small traffic
slice (e.g. 5%) **in parallel** with MoEngage on the *same* audience, guarantee no
user is double-sent, then prove on the conversion metric that the new system is
**not significantly worse** than MoEngage before cutting over.

Three pieces (per the survey's two hard requirements):

* ``splitter`` — deterministic, stable traffic split into ``shadow`` (new system)
  vs. ``control`` (MoEngage), built on ``growth_common.stable_fraction``.
* ``dedup`` — a middle-layer ``DedupLedger`` + ``reconcile`` so a user is never sent
  by *both* systems while they run in parallel (requirement 1).
* ``report`` — per-arm metrics, a two-proportion z-test (stdlib ``math`` only), and
  a ``compare`` that emits a ``ShadowReport`` with a non-inferiority verdict
  (requirement 2: an A/B comparison report ready when the campaign fires).

Public API::

    from shadow import assign_arm, split
    from shadow import DedupLedger, reconcile
    from shadow import arm_metrics, two_proportion_ztest, compare, ShadowReport

Zero third-party dependencies (stdlib + the shared ``growth_common`` contract).
"""
from .dedup import DedupLedger, reconcile
from .report import (
    ShadowReport,
    arm_metrics,
    compare,
    two_proportion_ztest,
)
from .splitter import CONTROL, SHADOW, assign_arm, split

__all__ = [
    "assign_arm",
    "split",
    "SHADOW",
    "CONTROL",
    "DedupLedger",
    "reconcile",
    "arm_metrics",
    "two_proportion_ztest",
    "compare",
    "ShadowReport",
]
__version__ = "0.1.0"
