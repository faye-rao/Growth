"""Deterministic in-memory sample dataset for tests and the demo.

Reference time is fixed (`NOW`) so frequency/time-window assertions are stable.
Models Botim-flavored attributes (KYC, wallet, balance) and events.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

NOW = datetime(2026, 6, 2, 12, 0, 0)


def _ev(customer_id: str, name: str, ts: datetime, **props: Any) -> Dict[str, Any]:
    return {"customer_id": customer_id, "event_name": name, "ts": ts, **props}


def build_sample_dataset() -> Dict[str, Any]:
    users = [
        {"customer_id": "u1", "is_kyc": True, "wallet_activated": False, "balance": 5000, "country": "AE", "device_height": 5, "platform": "iOS"},
        {"customer_id": "u2", "is_kyc": True, "wallet_activated": True, "balance": 200, "country": "IN", "device_height": 8, "platform": "Android"},
        {"customer_id": "u3", "is_kyc": False, "wallet_activated": False, "balance": 0, "country": "PH", "device_height": 5, "platform": "Android"},
        {"customer_id": "u4", "is_kyc": True, "wallet_activated": False, "balance": 1500, "country": "AE", "device_height": 5, "platform": "Android"},
        {"customer_id": "u5", "is_kyc": True, "wallet_activated": True, "balance": 9000, "country": "AE", "device_height": 8, "platform": "iOS"},
    ]

    events = [
        # u1 User Logout: 3 within last 3 days (2 with device_height=5), 1 old (outside window)
        _ev("u1", "User Logout", datetime(2026, 6, 1, 3, 0), device_height=5),
        _ev("u1", "User Logout", datetime(2026, 6, 1, 14, 0), device_height=5),
        _ev("u1", "User Logout", datetime(2026, 5, 31, 23, 0), device_height=8),
        _ev("u1", "User Logout", datetime(2026, 4, 1, 9, 0), device_height=5),  # old
        # u3 User Logout: 1 within window, device_height=8 -> predominantly(dh=5) is False
        _ev("u3", "User Logout", datetime(2026, 6, 1, 10, 0), device_height=8),
        # Push ID Register Android within window
        _ev("u2", "Push ID Register Android", datetime(2026, 6, 1, 10, 0)),
        _ev("u4", "Push ID Register Android", datetime(2026, 5, 20, 10, 0)),  # old
        # App Opened
        _ev("u2", "App Opened", datetime(2026, 6, 2, 9, 0)),
        _ev("u5", "App Opened", datetime(2026, 6, 2, 8, 0)),
        # Transfer (for "KYC but no transfer in 90d" cohort): u2 & u5 have transfers, u1/u4 none
        _ev("u2", "Transfer", datetime(2026, 5, 15, 12, 0), amount=300),
        _ev("u5", "Transfer", datetime(2026, 6, 1, 12, 0), amount=1200),
    ]
    return {"users": users, "events": events}
