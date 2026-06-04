"""Botim Growth Platform — service decomposition.

The 9 modules are exposed as **independent FastAPI services** grouped by
functional cohesion (NOT one monolith). Each ``services/<name>.py`` exposes a
module-level ``app`` that is runnable on its own::

    uvicorn services.audience:app
    uvicorn services.campaign:app

Grouping rationale (functional independence / who scales together):

* ``data``        — M8 Data Foundation (identity, suppression, ingest, DQC).
* ``audience``    — M2 Cohort Engine (segmentation / NL2SQL / templates).
* ``personalize`` — M5 1-to-1 personalization (low-latency, app-facing).
* ``campaign``    — M3 orchestration + M1 messaging (audience -> deliver).
* ``content``     — M6 AI copywriting + compliance.
* ``analytics``   — M4 funnel/attribution + M9 behavioral reports/insights.
* ``experiment``  — M7 shadow validation (the MoEngage cut-over gate).

``SERVICES`` is the registry the API gateway uses to mount/route. Each entry is
``name -> (url_prefix, app)``.
"""
from __future__ import annotations

from . import (
    analytics,
    audience,
    campaign,
    content,
    data_platform,
    experiment,
    personalization,
)

# name -> (mount prefix, FastAPI app)
SERVICES = {
    "data": ("/api/data", data_platform.app),
    "audience": ("/api/audience", audience.app),
    "personalize": ("/api/personalize", personalization.app),
    "campaign": ("/api/campaign", campaign.app),
    "content": ("/api/content", content.app),
    "analytics": ("/api/analytics", analytics.app),
    "experiment": ("/api/experiment", experiment.app),
}

__all__ = [
    "SERVICES",
    "data_platform",
    "audience",
    "personalization",
    "campaign",
    "content",
    "analytics",
    "experiment",
]
