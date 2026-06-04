"""M6 copy providers — the pluggable generation backend.

Since we can't call a real LLM in this environment, M6 is built around a
**pluggable, deterministic, offline** provider interface: a :class:`CopyProvider`
``Protocol`` with a stdlib :class:`TemplateProvider` implementation. A real LLM
provider can be injected later behind the *same* interface (the generator only
depends on the protocol).

``TemplateProvider`` produces localized copy from per-(goal, locale) templates
with light token substitution (product / tone / CTA). It is **deterministic**
(same request + seed -> identical text) yet yields **different** text for
different ``seed`` (so N variants differ) and for different ``locales``. Stdlib
only.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Protocol, runtime_checkable

from .models import AR, EN, HI, TL, CopyRequest


@runtime_checkable
class CopyProvider(Protocol):
    """The generation backend contract.

    Implementations return a single copy string for ``(request, locale, seed)``.
    The same triple must always return the same text (determinism), while
    different ``seed`` values should yield different phrasings.
    """

    def generate(self, request: CopyRequest, locale: str, seed: int = 0) -> str:
        ...


# Per-(goal, locale) headline/body templates. ``{product}`` / ``{cta}`` are the
# substitution tokens. A "default" goal entry is the fallback for unknown goals.
_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "activate_wallet": {
        EN: [
            "Activate your Botim {product} today and {cta}.",
            "Your Botim {product} is ready — {cta} in seconds.",
            "Turn on Botim {product} now and {cta}.",
        ],
        AR: [
            "فعّل محفظة {product} من بوتيم اليوم و{cta}.",
            "محفظة {product} جاهزة — {cta} في ثوانٍ.",
            "شغّل {product} من بوتيم الآن و{cta}.",
        ],
        HI: [
            "अपना Botim {product} आज ही चालू करें और {cta}।",
            "आपका Botim {product} तैयार है — कुछ ही पल में {cta}।",
            "अभी Botim {product} ऑन करें और {cta}।",
        ],
        TL: [
            "I-activate ang iyong Botim {product} ngayon at {cta}.",
            "Handa na ang Botim {product} mo — {cta} sa ilang segundo.",
            "Buksan ang Botim {product} ngayon at {cta}.",
        ],
    },
    "default": {
        EN: [
            "Discover Botim {product} and {cta}.",
            "Get more from Botim {product} — {cta} today.",
            "Make the most of Botim {product}: {cta}.",
        ],
        AR: [
            "اكتشف {product} من بوتيم و{cta}.",
            "احصل على المزيد من {product} — {cta} اليوم.",
            "استفد من {product} من بوتيم: {cta}.",
        ],
        HI: [
            "Botim {product} खोजें और {cta}।",
            "Botim {product} से और पाएं — आज ही {cta}।",
            "Botim {product} का पूरा लाभ लें: {cta}।",
        ],
        TL: [
            "Tuklasin ang Botim {product} at {cta}.",
            "Higit pa mula sa Botim {product} — {cta} ngayon.",
            "Samantalahin ang Botim {product}: {cta}.",
        ],
    },
}

# Per-locale CTA phrasings, indexed deterministically by seed.
_CTAS: Dict[str, List[str]] = {
    EN: ["start sending money", "unlock instant transfers", "save on every transfer"],
    AR: ["ابدأ تحويل الأموال", "استمتع بتحويلات فورية", "وفّر في كل تحويل"],
    HI: ["पैसे भेजना शुरू करें", "तुरंत ट्रांसफर पाएं", "हर ट्रांसफर पर बचत करें"],
    TL: ["magpadala ng pera", "mag-transfer agad", "makatipid sa bawat padala"],
}

# Per-locale tone prefix, appended for non-"friendly" tones to vary wording.
_TONE_PREFIX: Dict[str, Dict[str, str]] = {
    "urgent": {EN: "Don't miss out! ", AR: "لا تفوّت الفرصة! ", HI: "मौका न चूकें! ", TL: "Huwag palampasin! "},
    "formal": {EN: "We invite you to ", AR: "ندعوك إلى ", HI: "हम आपको आमंत्रित करते हैं: ", TL: "Inaanyayahan ka naming "},
}


def _index(parts: object, modulo: int) -> int:
    """Deterministic index in ``[0, modulo)`` from ``parts`` (stdlib sha256).

    Mirrors ``growth_common.stable_fraction`` so selection is stable across runs
    and processes (unlike the salted built-in ``hash``).
    """
    if modulo <= 0:
        return 0
    key = str(parts).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    n = int.from_bytes(digest[:8], "big")
    return n % modulo


class TemplateProvider:
    """Deterministic, offline template-based copy provider (stdlib only).

    Selects a (goal, locale) template, a CTA and (optionally) a tone prefix using
    a stable hash of ``(goal, product, locale, tone, seed)`` so that:

    * same inputs -> identical output (determinism),
    * different ``seed`` -> different template/CTA pick (N variants differ),
    * different ``locale`` -> different language template (locales differ).
    """

    def generate(self, request: CopyRequest, locale: str, seed: int = 0) -> str:
        goal_templates = _TEMPLATES.get(request.goal, _TEMPLATES["default"])
        templates = goal_templates.get(locale) or _TEMPLATES["default"].get(locale)
        if not templates:
            # Locale validated by CopyRequest, but guard anyway.
            templates = _TEMPLATES["default"][EN]

        ctas = _CTAS.get(locale, _CTAS[EN])

        t_idx = _index(("tpl", request.goal, request.product, locale, seed), len(templates))
        c_idx = _index(("cta", request.goal, request.product, locale, seed), len(ctas))

        text = templates[t_idx].format(product=request.product, cta=ctas[c_idx])

        prefix = _TONE_PREFIX.get(request.tone, {}).get(locale, "")
        if prefix:
            text = prefix + text
        return text


__all__ = ["CopyProvider", "TemplateProvider"]
