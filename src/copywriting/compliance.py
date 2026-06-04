"""M6 compliance / safety check for marketing copy (fintech context).

Botim is a fintech app, so generated copy must pass a safety gate before it can
ship. :func:`check` applies a small set of rules and **auto-fixes** where it can,
returning a :class:`ComplianceResult` whose ``fixed_text`` is the shippable copy
and whose ``ok`` is ``True`` only if no *hard* violation remains after auto-fix.

Rules:

* **banned claims** — forbidden words/phrases (e.g. ``"guaranteed"``,
  ``"risk-free"``, ``"100% approved"``) are a hard violation (can't be safely
  auto-removed without changing meaning).
* **over length** — per-channel max length (push ~120, sms ~160, in_app ~240);
  flagged and **auto-truncated** in ``fixed_text`` (soft — fixed).
* **missing disclaimer** — products in ``{"Loan", "Remittance"}`` require a short
  fintech disclaimer; appended if missing (soft — fixed).
* **shouting** — ALL-CAPS copy is a hard violation (not auto-fixed).

Zero third-party deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Channel -> max characters. ``None`` channel means no length limit.
CHANNEL_MAX_LEN = {
    "push": 120,
    "sms": 160,
    "in_app": 240,
}

# Forbidden absolute/guarantee-style claims (matched case-insensitively).
BANNED_CLAIMS = (
    "guaranteed",
    "risk-free",
    "risk free",
    "100% approved",
    "100 percent approved",
    "no risk",
    "guarantee",
)

# Products that legally require a disclaimer in their copy.
DISCLAIMER_PRODUCTS = ("Loan", "Remittance")
DISCLAIMER_TEXT = "T&Cs apply."

# Fraction of letters that must be upper-case (over a length threshold) to count
# as ALL-CAPS shouting.
_SHOUT_MIN_LETTERS = 12
_SHOUT_RATIO = 0.9


@dataclass
class ComplianceResult:
    """Outcome of a compliance check.

    ``ok`` — no hard violation remains after auto-fix; ``violations`` — human
    readable codes/messages for everything flagged (including the ones that were
    auto-fixed); ``fixed_text`` — the shippable copy after truncation / disclaimer
    insertion.
    """

    ok: bool
    violations: List[str] = field(default_factory=list)
    fixed_text: str = ""


def _is_shouting(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < _SHOUT_MIN_LETTERS:
        return False
    # Only meaningful for cased scripts; Arabic/Hindi letters have no upper case
    # and ``isupper()`` is False for them, so they never trip this rule.
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) >= _SHOUT_RATIO


def check(
    text: str,
    *,
    channel: Optional[str] = None,
    product: Optional[str] = None,
) -> ComplianceResult:
    """Run the compliance gate over ``text`` and return a :class:`ComplianceResult`.

    Hard violations (banned claim, shouting) leave ``ok=False``; soft violations
    (over length, missing disclaimer) are auto-fixed and do not, on their own,
    fail the result.
    """
    violations: List[str] = []
    hard = False
    fixed = text

    # --- banned claims (hard) -------------------------------------------------
    lowered = fixed.lower()
    for term in BANNED_CLAIMS:
        if term in lowered:
            violations.append(f"banned_claim:{term}")
            hard = True

    # --- shouting / ALL-CAPS (hard) ------------------------------------------
    if _is_shouting(fixed):
        violations.append("shouting_all_caps")
        hard = True

    # --- missing fintech disclaimer (soft, auto-append) ----------------------
    needs_disclaimer = (
        product in DISCLAIMER_PRODUCTS and DISCLAIMER_TEXT.lower() not in fixed.lower()
    )
    if needs_disclaimer:
        violations.append("missing_disclaimer")
        sep = "" if fixed.endswith(" ") else " "
        fixed = f"{fixed}{sep}{DISCLAIMER_TEXT}"

    # --- over length (soft, auto-truncate) -----------------------------------
    # A required disclaimer must SURVIVE truncation, so we truncate the body and
    # re-append the disclaimer rather than chopping it off the end (compliance).
    limit = CHANNEL_MAX_LEN.get(channel) if channel else None
    if limit is not None and len(fixed) > limit and limit >= 1:
        violations.append(f"over_length:{len(fixed)}>{limit}")
        disclaimer_required = product in DISCLAIMER_PRODUCTS
        if disclaimer_required:
            tail = " " + DISCLAIMER_TEXT
            body_budget = max(0, limit - len(tail) - 1)  # -1 for the ellipsis
            body = _strip_disclaimer(fixed)
            fixed = (body[:body_budget].rstrip() + "…" + tail)
            if len(fixed) > limit:  # disclaimer alone exceeds the channel limit
                fixed = fixed[:limit]
        else:
            fixed = fixed[: max(0, limit - 1)].rstrip() + "…"
            if len(fixed) > limit:
                fixed = fixed[:limit]

    # a required disclaimer that got lost (e.g. limit too small) is a hard fail
    if product in DISCLAIMER_PRODUCTS and DISCLAIMER_TEXT.lower() not in fixed.lower():
        if "disclaimer_lost_to_truncation" not in violations:
            violations.append("disclaimer_lost_to_truncation")
        hard = True

    ok = not hard
    return ComplianceResult(ok=ok, violations=violations, fixed_text=fixed)


def _strip_disclaimer(text: str) -> str:
    """Remove a trailing disclaimer (and separators) so we can re-place it."""
    idx = text.lower().rfind(DISCLAIMER_TEXT.lower())
    if idx == -1:
        return text
    return text[:idx].rstrip()


__all__ = [
    "ComplianceResult",
    "check",
    "CHANNEL_MAX_LEN",
    "BANNED_CLAIMS",
    "DISCLAIMER_PRODUCTS",
    "DISCLAIMER_TEXT",
]
