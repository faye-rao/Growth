"""M6 copy generator — orchestrates provider + compliance, emits M3 variants.

:class:`CopyGenerator` ties a pluggable :class:`~copywriting.provider.CopyProvider`
to the compliance gate: for each requested locale it asks the provider for ``n``
variants (distinct seeds so they differ), runs each through
:func:`copywriting.compliance.check`, and stores the compliance outcome in the
variant ``meta`` while using the auto-fixed text as the final copy.

:func:`to_orchestration_variants` maps generated copy to **M3 Variant-style
dicts** (``name`` like ``"A"``/``"B"``, ``weight``, ``content_id`` and a
per-locale ``payload``) so the output feeds the M3 A/B/n allocator directly.
Zero third-party deps.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .compliance import check
from .models import CopyRequest, CopyVariant
from .provider import CopyProvider

# Variant names "A".."Z" for A/B/n arms, matching M3's free-form name field.
_NAMES = [chr(ord("A") + i) for i in range(26)]


class CopyGenerator:
    """Generate compliant, multilingual A/B/n copy from a :class:`CopyRequest`.

    ``provider`` is any :class:`CopyProvider` (the stdlib
    :class:`~copywriting.provider.TemplateProvider`, or a real LLM later).
    ``compliance_channel_default`` is used for the length check when a request
    carries no ``channel``.
    """

    def __init__(
        self,
        provider: CopyProvider,
        *,
        compliance_channel_default: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.compliance_channel_default = compliance_channel_default

    def generate(self, request: CopyRequest, n: int = 2) -> List[CopyVariant]:
        """Return ``n`` compliant variants **per requested locale**.

        Each variant uses a distinct ``seed`` (``0..n-1``) so the N arms differ;
        each is passed through compliance, with the outcome stored in ``meta`` and
        the auto-fixed text used as the final ``text``.
        """
        if n < 1:
            raise ValueError("n must be >= 1")

        channel = request.channel or self.compliance_channel_default
        variants: List[CopyVariant] = []
        for locale in request.locales:
            for seed in range(n):
                raw = self.provider.generate(request, locale, seed=seed)
                result = check(raw, channel=channel, product=request.product)
                variants.append(
                    CopyVariant(
                        locale=locale,
                        text=result.fixed_text,
                        meta={
                            "seed": seed,
                            "goal": request.goal,
                            "product": request.product,
                            "tone": request.tone,
                            "channel": channel,
                            "compliant": result.ok,
                            "violations": list(result.violations),
                            "raw_text": raw,
                        },
                    )
                )
        return variants

    def to_orchestration_variants(
        self,
        variants: List[CopyVariant],
        content_ids: Optional[List[str]] = None,
        weights: Optional[List[float]] = None,
    ) -> List[Dict]:
        """Map generated copy to M3 ``Variant``-style dicts (one arm per seed).

        Variants are grouped by ``seed`` into A/B/n arms; each arm carries a
        per-locale ``payload`` (``{locale: text}``). Returns a list of dicts shaped
        like ``orchestration.models.Variant`` plus a ``payload`` field::

            {"name": "A", "weight": 1.0, "content_id": "...", "payload": {...}}

        ``content_ids`` / ``weights`` (positional per arm) override the defaults.
        """
        # Group texts by seed -> arm index, preserving locale order.
        by_seed: Dict[int, Dict[str, str]] = {}
        for v in variants:
            seed = v.meta.get("seed", 0)
            by_seed.setdefault(seed, {})[v.locale] = v.text

        arms: List[Dict] = []
        for arm_idx, seed in enumerate(sorted(by_seed)):
            if arm_idx >= len(_NAMES):
                raise ValueError("too many arms (max 26 A/B/n variants)")
            name = _NAMES[arm_idx]
            if content_ids and arm_idx < len(content_ids):
                content_id = content_ids[arm_idx]
            else:
                content_id = f"copy_{name}"
            if weights and arm_idx < len(weights):
                weight = float(weights[arm_idx])
            else:
                weight = 1.0
            arms.append(
                {
                    "name": name,
                    "weight": weight,
                    "content_id": content_id,
                    "payload": dict(by_seed[seed]),
                }
            )
        return arms


__all__ = ["CopyGenerator"]
