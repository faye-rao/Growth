"""M6 AI Copywriting data models — copy request / generated variant.

Per the survey, growth's incremental value over MoEngage comes from **AI**: M6
generates **multilingual marketing copy** (Botim's markets — English / Arabic /
Hindi / Tagalog), runs a fintech **compliance / safety check**, closes a
copy↔effect **feedback loop**, and emits **A/B/n variants** that feed M3
orchestration.

A ``CopyRequest`` describes *what* to write (goal + product + target locales +
tone). A ``CopyVariant`` is one generated piece of copy for one locale, carrying
``meta`` (seed, compliance outcome, channel, ...). Zero third-party deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Botim's launch markets (the locales M6 can write copy for).
EN = "en"
AR = "ar"
HI = "hi"
TL = "tl"
SUPPORTED_LOCALES = (EN, AR, HI, TL)


@dataclass
class CopyRequest:
    """A request to generate marketing copy.

    ``goal`` is the growth objective (e.g. ``"activate_wallet"``); ``product`` is
    the Botim product (``"Wallet"`` / ``"Loan"`` / ``"Remittance"``); ``locales``
    is a subset of :data:`SUPPORTED_LOCALES`; ``tone`` shapes the wording
    (``"friendly"`` / ``"urgent"`` / ``"formal"``); ``channel`` (push / sms /
    in_app) and ``max_len`` flow into the compliance length check.
    """

    goal: str
    product: str
    locales: List[str]
    tone: str = "friendly"
    channel: Optional[str] = None
    max_len: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.goal:
            raise ValueError("goal must be non-empty")
        if not self.product:
            raise ValueError("product must be non-empty")
        if not self.locales:
            raise ValueError("at least one locale is required")
        bad = [loc for loc in self.locales if loc not in SUPPORTED_LOCALES]
        if bad:
            raise ValueError(
                f"unsupported locale(s) {bad}; supported: {SUPPORTED_LOCALES}"
            )
        if self.max_len is not None and self.max_len <= 0:
            raise ValueError("max_len must be positive when set")


@dataclass
class CopyVariant:
    """One generated piece of copy for one locale.

    ``meta`` carries provenance and the compliance outcome — e.g. ``seed``,
    ``goal``, ``product``, ``tone``, ``channel``, ``compliant`` (bool),
    ``violations`` (list[str]) and ``raw_text`` (pre-compliance text). ``text`` is
    always the *final* (post auto-fix) copy.
    """

    locale: str
    text: str
    meta: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CopyRequest",
    "CopyVariant",
    "SUPPORTED_LOCALES",
    "EN",
    "AR",
    "HI",
    "TL",
]
