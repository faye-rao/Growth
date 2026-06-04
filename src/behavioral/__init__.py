"""M9 — Behavioral Analytics (deliberately scoped-down).

Per the survey, M9 is **intentionally minimal**: full dashboards are the data
team's job and the product side already has Amplitude, so this module is *not* a
general BI tool. It only does three things:

1. **Canonical reports** (`reports.py`) — reproduces the handful of reports
   operators actually view day-to-day (active users, new vs returning, event
   volume, campaign performance, a conversion funnel, retention).
2. **Auto-insights** (`auto_insights.py`) — lightweight automated analysis that
   flags period-over-period spikes/drops with a short narrative.
3. **MoEngage metric replacements** (`metrics.py`) — self-built RFM / engagement
   / churn-risk so consumers that depend on those MoEngage internal metrics
   aren't broken when MoEngage is dropped.

Funnel/attribution logic is **reused from M4** (`analytics`), never duplicated.
Zero third-party dependencies (stdlib only).
"""
from __future__ import annotations

from .auto_insights import Insight, compare_periods, detect_insights
from .metrics import (
    ChurnRisk,
    EngagementScore,
    RfmScore,
    churn_risk,
    engagement_score,
    rfm_scores,
)
from .reports import (
    active_users,
    campaign_performance,
    conversion_funnel_report,
    event_volume,
    new_vs_returning,
    retention_lite,
)

__all__ = [
    # reports
    "active_users",
    "new_vs_returning",
    "event_volume",
    "campaign_performance",
    "conversion_funnel_report",
    "retention_lite",
    # auto-insights
    "detect_insights",
    "compare_periods",
    "Insight",
    # metrics
    "rfm_scores",
    "engagement_score",
    "churn_risk",
    "RfmScore",
    "EngagementScore",
    "ChurnRisk",
]
