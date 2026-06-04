"""Shared in-memory demo world for the decomposed services.

Each service is independently runnable and backs itself with the in-memory
sample dataset (the same pattern as ``cohort_engine.api``). For the demo we
need a single dataset that is simultaneously:

* a valid **M2 cohort** dataset (users carry ``is_kyc`` / ``balance`` /
  ``wallet_activated`` / ``country`` attributes + behavioral events), and
* a valid **M1 messaging** dataset (users carry ``push_token`` / ``phone`` /
  ``last_active`` / ``app_uninstalled`` so the real Gateway can decide
  reachability).

This mirrors ``examples/e2e_demo.build_world`` so the campaign service can
resolve an audience via :class:`CohortEngine` and deliver it through the real
messaging :class:`Gateway` in one process.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

# Fixed reference time shared across modules (matches cohort/messaging sample data).
NOW = datetime(2026, 6, 2, 12, 0, 0)


def build_world() -> Dict[str, Any]:
    """A deterministic dataset valid for both cohort segmentation and messaging."""
    recent = NOW - timedelta(days=1)

    def u(cid, kyc, bal, wallet, country, token, uninstalled=False):
        return {
            "customer_id": cid,
            "is_kyc": kyc,
            "balance": bal,
            "wallet_activated": wallet,
            "country": country,
            "push_token": token,
            "phone": "+9715" + cid[-1],
            "last_active": recent,
            "app_uninstalled": uninstalled,
        }

    users = [
        u("w1", True, 5000, False, "AE", "t1"),                    # cohort, healthy -> SENT
        u("w2", True, 3000, False, "AE", "t2"),                    # cohort, opted-out
        u("w3", True, 2000, False, "IN", "t3", uninstalled=True),  # cohort, unreachable
        u("w4", True, 1500, False, "AE", None),                    # cohort, no push_token
        u("w5", True, 1200, False, "PH", "t5"),                    # cohort, healthy -> SENT
        u("w6", True, 200, True, "AE", "t6"),                      # not cohort (low bal)
        u("w7", False, 0, False, "PH", "t7"),                      # not cohort (no kyc)
        u("w8", True, 8000, True, "AE", "t8"),                     # not cohort (wallet on)
    ]

    def ev(cid, name, ts, **kw):
        return {"customer_id": cid, "event_name": name, "ts": ts, **kw}

    j1 = datetime(2026, 6, 1)
    events = [
        ev("w1", "Call Made", datetime(2026, 5, 25)),
        ev("w5", "Call Made", datetime(2026, 5, 28)),
        ev("w4", "Call Made", datetime(2026, 5, 30)),
        ev("w8", "Call Made", datetime(2026, 5, 26)),
        ev("w1", "App Opened", j1.replace(hour=10)),
        ev("w5", "App Opened", j1.replace(hour=9)),
        ev("w4", "App Opened", j1.replace(hour=8)),
        ev("w6", "App Opened", j1.replace(hour=7)),
        ev("w8", "App Opened", j1.replace(hour=6)),
        ev("w1", "Transfer", NOW + timedelta(hours=6), converted=True),
        ev("w5", "Transfer", NOW + timedelta(hours=20), converted=True),
        ev("w8", "Transfer", j1.replace(hour=20)),
    ]
    return {"users": users, "events": events}


# A high-value-cohort spec that selects w1..w5 from build_world() (KYC, balance>=1000,
# wallet not yet activated) — the canonical campaign audience for the demo.
HIGH_VALUE_SPEC: Dict[str, Any] = {
    "name": "high_value_kyc_no_wallet",
    "match": {
        "op": "and",
        "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
            {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
        ],
    },
}
