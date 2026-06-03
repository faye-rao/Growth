"""Deterministic messaging dataset for tests and the demo.

Reference time is fixed (`NOW`) so reachability (stale ``last_active``) checks
are stable. Each user carries the M1-relevant delivery attributes:
``push_token``, ``phone``, ``last_active`` (datetime), ``app_uninstalled``.

The fixed user set is engineered to exercise every pipeline branch:

| user | outcome under a push send |
|------|---------------------------|
| m1   | healthy → SENT via push |
| m2   | opted out → SUPPRESSED_OPTOUT |
| m3   | app uninstalled → SUPPRESSED_UNREACHABLE |
| m4   | stale last_active → SUPPRESSED_UNREACHABLE |
| m5   | no push_token, but has phone → SUPPRESSED_UNREACHABLE for push;
         reachable for sms/in_app |
| m6   | healthy but no push_token → push fails, falls back to sms → SENT |
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Set

# Fixed reference time (aligned with the M2 cohort sample dataset's NOW).
NOW = datetime(2026, 6, 2, 12, 0, 0)

# Default reachability threshold: inactive longer than this == unreachable.
STALE_AFTER_DAYS = 30

# Users who have opted out of marketing messages (gateway suppression set).
OPT_OUT: Set[str] = {"m2"}


def build_messaging_dataset() -> Dict[str, Any]:
    recent = NOW - timedelta(days=1)
    stale = NOW - timedelta(days=90)
    users = [
        {"customer_id": "m1", "push_token": "tok-m1", "phone": "+971500000001",
         "last_active": recent, "app_uninstalled": False},
        {"customer_id": "m2", "push_token": "tok-m2", "phone": "+971500000002",
         "last_active": recent, "app_uninstalled": False},
        {"customer_id": "m3", "push_token": "tok-m3", "phone": "+971500000003",
         "last_active": recent, "app_uninstalled": True},
        {"customer_id": "m4", "push_token": "tok-m4", "phone": "+971500000004",
         "last_active": stale, "app_uninstalled": False},
        {"customer_id": "m5", "push_token": None, "phone": "+971500000005",
         "last_active": recent, "app_uninstalled": False},
        {"customer_id": "m6", "push_token": None, "phone": "+971500000006",
         "last_active": recent, "app_uninstalled": False},
    ]
    return {"users": users}
