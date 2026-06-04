"""M6 copy↔effect feedback loop — learn which copy converts.

The output of M6 (A/B/n copy variants) is delivered by M1/M3, which log
``growth_common.DeliveryRecord`` rows tagged with the winning ``variant`` name.
This module closes the loop: it ranks variants by **conversion rate** (CVR) over
their *sent* records and selects the best arm to scale, with a deterministic
epsilon-greedy explore/exploit option.

* :func:`rank_by_performance` — ``(variant, sent, conversions, cvr)`` sorted by
  CVR desc (CVR = converted / sent among ``SENT``; ``/0`` guarded to ``0.0``).
* :func:`select_best` — the highest-CVR variant name (``None`` if no data).
* :func:`epsilon_greedy` — deterministic explore/exploit given a ``tie_breaker``.

Zero third-party deps (only the shared ``growth_common`` contract).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from growth_common import DeliveryRecord, DeliveryStatus  # noqa: F401  (DeliveryStatus part of the contract)

# (variant_name, sent, conversions, cvr)
PerfRow = Tuple[str, int, int, float]


def rank_by_performance(records: List[DeliveryRecord]) -> List[PerfRow]:
    """Rank variants by conversion rate (CVR) over their **sent** records.

    Only ``SENT`` records count toward ``sent``; ``conversions`` are sent records
    with ``converted=True``; ``cvr = conversions / sent`` (``0.0`` when no sent —
    no ``ZeroDivisionError``). Sorted by CVR desc, then by ``sent`` desc, then by
    variant name for a stable, deterministic order.
    """
    sent_by: dict = {}
    conv_by: dict = {}
    for r in records:
        if not r.is_sent:
            continue
        sent_by[r.variant] = sent_by.get(r.variant, 0) + 1
        if r.converted:
            conv_by[r.variant] = conv_by.get(r.variant, 0) + 1

    rows: List[PerfRow] = []
    for variant, sent in sent_by.items():
        conversions = conv_by.get(variant, 0)
        cvr = conversions / sent if sent else 0.0
        rows.append((variant, sent, conversions, cvr))

    rows.sort(key=lambda row: (-row[3], -row[1], row[0]))
    return rows


def select_best(records: List[DeliveryRecord]) -> Optional[str]:
    """Return the highest-CVR variant name, or ``None`` when there is no data."""
    ranked = rank_by_performance(records)
    return ranked[0][0] if ranked else None


def epsilon_greedy(
    records: List[DeliveryRecord],
    *,
    epsilon: float = 0.1,
    tie_breaker: Optional[str] = None,
) -> Optional[str]:
    """Deterministic epsilon-greedy variant choice (no randomness).

    Models explore/exploit deterministically and testably:

    * ``epsilon <= 0`` -> always **exploit** the best-CVR variant.
    * ``epsilon >= 1`` -> always **explore**: return ``tie_breaker`` if it is a
      known variant, else the *second*-best variant (the lowest-CVR known variant
      if only one alternative exists), else the best.
    * ``0 < epsilon < 1`` -> exploit (best). The probabilistic split is left to
      the caller / online layer; here we stay deterministic so tests are stable.

    Returns ``None`` only when there are no records at all.
    """
    if not (0.0 <= epsilon <= 1.0):
        raise ValueError("epsilon must be in [0, 1]")

    ranked = rank_by_performance(records)
    if not ranked:
        return None

    names = [row[0] for row in ranked]
    best = names[0]

    if epsilon >= 1.0:
        if tie_breaker is not None and tie_breaker in names:
            return tie_breaker
        # Deterministic exploration: the next-best arm if one exists.
        return names[1] if len(names) > 1 else best

    # epsilon < 1 (including 0): exploit the best variant.
    return best


__all__ = [
    "rank_by_performance",
    "select_best",
    "epsilon_greedy",
    "PerfRow",
]
