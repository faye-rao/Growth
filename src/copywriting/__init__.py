"""Botim Growth Platform — M6 AI Copywriting (MVP).

Per the survey, growth's incremental value over MoEngage comes from **AI**. M6
generates **multilingual marketing copy** (Botim's markets — English / Arabic /
Hindi / Tagalog), runs a fintech **compliance / safety check**, closes a
copy↔effect **feedback loop** (learn which copy converts) and emits **A/B/n
variants** that feed M3 orchestration.

Since a real LLM can't be called here, M6 is built **deterministic, offline and
pluggable**: a :class:`CopyProvider` ``Protocol`` with a stdlib
:class:`TemplateProvider`; a real LLM provider can be injected later behind the
same interface.

Public API::

    from copywriting import CopyRequest, CopyVariant
    from copywriting import TemplateProvider, CopyGenerator
    from copywriting import check               # compliance gate
    from copywriting import rank_by_performance, select_best, epsilon_greedy

    gen = CopyGenerator(TemplateProvider(), compliance_channel_default="push")
    req = CopyRequest(goal="activate_wallet", product="Wallet",
                      locales=["en", "ar"], tone="friendly")
    variants = gen.generate(req, n=2)           # 2 arms x 2 locales, compliant
    arms = gen.to_orchestration_variants(variants)   # -> M3 Variant-style dicts

    # later, after M1/M3 deliver and log DeliveryRecords:
    best = select_best(records)                 # highest-CVR copy arm

Zero third-party dependencies (stdlib + the shared ``growth_common`` contract).
"""
from .compliance import (
    BANNED_CLAIMS,
    CHANNEL_MAX_LEN,
    DISCLAIMER_PRODUCTS,
    DISCLAIMER_TEXT,
    ComplianceResult,
    check,
)
from .feedback import epsilon_greedy, rank_by_performance, select_best
from .generator import CopyGenerator
from .models import (
    AR,
    EN,
    HI,
    SUPPORTED_LOCALES,
    TL,
    CopyRequest,
    CopyVariant,
)
from .provider import CopyProvider, TemplateProvider

__all__ = [
    # models
    "CopyRequest",
    "CopyVariant",
    "SUPPORTED_LOCALES",
    "EN",
    "AR",
    "HI",
    "TL",
    # provider
    "CopyProvider",
    "TemplateProvider",
    # compliance
    "check",
    "ComplianceResult",
    "CHANNEL_MAX_LEN",
    "BANNED_CLAIMS",
    "DISCLAIMER_PRODUCTS",
    "DISCLAIMER_TEXT",
    # generator
    "CopyGenerator",
    # feedback
    "rank_by_performance",
    "select_best",
    "epsilon_greedy",
]
__version__ = "0.1.0"
