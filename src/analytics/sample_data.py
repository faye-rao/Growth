"""Deterministic in-memory sample data for M4 funnel/attribution tests & demo.

Reference time is fixed (`NOW`) so window assertions are stable. Reuses the
shared event record shape (`{"customer_id","event_name","ts", ...}`) and the
`DeliveryRecord` touch-log contract from `growth_common`.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from growth_common import Channel, DeliveryRecord, DeliveryStatus

NOW = datetime(2026, 6, 2, 12, 0, 0)


def _ev(customer_id: str, name: str, ts: datetime, **props: Any) -> Dict[str, Any]:
    return {"customer_id": customer_id, "event_name": name, "ts": ts, **props}


# --- cross-product funnel events: Call -> Wallet -> Remittance ----------------
def build_cross_product_events() -> List[Dict[str, Any]]:
    """Synthetic Call -> Wallet -> Remittance journey across product lines.

    - u1: all three steps, in order, quickly  -> reaches step 3
    - u2: Call + Wallet only                  -> reaches step 2
    - u3: Call only                           -> reaches step 1
    - u4: did Wallet BEFORE Call (out of order) -> reaches step 0 (not counted)
    - u5: Call + Wallet in order, Remittance too LATE (used with within_days)
    """
    base = datetime(2026, 6, 1, 9, 0)
    return [
        # u1 — full conversion, tightly sequenced
        _ev("u1", "Call Active", base),
        _ev("u1", "Wallet Register", base + timedelta(hours=2)),
        _ev("u1", "Remittance First Txn", base + timedelta(hours=5)),
        # u2 — drops after Wallet
        _ev("u2", "Call Active", base + timedelta(hours=1)),
        _ev("u2", "Wallet Register", base + timedelta(hours=3)),
        # u3 — drops after Call
        _ev("u3", "Call Active", base + timedelta(hours=1)),
        # u4 — Wallet happened BEFORE Call: out of order, never enters funnel
        _ev("u4", "Wallet Register", base - timedelta(hours=2)),
        _ev("u4", "Call Active", base),
        # u5 — Call + Wallet in order; Remittance 10 days later (late for window)
        _ev("u5", "Call Active", base),
        _ev("u5", "Wallet Register", base + timedelta(hours=4)),
        _ev("u5", "Remittance First Txn", base + timedelta(days=10)),
    ]


# --- attribution: touch log + conversion events -------------------------------
def build_attribution_data() -> Dict[str, Any]:
    """Touch log (DeliveryRecord) + conversion events for attribution tests.

    - u1: SENT by camp_A then camp_B before converting (last vs first differ)
    - u2: only a FAILED touch before converting (must NOT attribute)
    - u3: SENT by camp_A, converts but OUTSIDE the window (must NOT attribute)
    """
    base = datetime(2026, 6, 1, 8, 0)
    deliveries = [
        DeliveryRecord("u1", "camp_A", Channel.PUSH, "c1", base, DeliveryStatus.SENT),
        DeliveryRecord(
            "u1", "camp_B", Channel.SMS, "c2", base + timedelta(hours=2),
            DeliveryStatus.SENT,
        ),
        DeliveryRecord(
            "u2", "camp_A", Channel.PUSH, "c1", base, DeliveryStatus.FAILED,
        ),
        DeliveryRecord("u3", "camp_A", Channel.PUSH, "c1", base, DeliveryStatus.SENT),
    ]
    conversions = [
        # u1 converts 3h after first touch -> within a 24h window
        _ev("u1", "Conversion", base + timedelta(hours=3)),
        # u2 converts but only had a FAILED touch
        _ev("u2", "Conversion", base + timedelta(hours=1)),
        # u3 converts 48h later -> outside a 24h window
        _ev("u3", "Conversion", base + timedelta(hours=48)),
    ]
    return {"deliveries": deliveries, "conversions": conversions}
