"""Shared contracts for the Botim Growth Platform modules (M1/M3/M4).

Keeping these in one place lets the messaging (M1), orchestration (M3) and
funnel/analytics (M4) modules develop against a stable interface and interoperate.
Zero third-party dependencies.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Protocol, runtime_checkable


# --- channels -----------------------------------------------------------------
class Channel:
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"
    ALL = ("push", "sms", "in_app")


# --- delivery outcome statuses ------------------------------------------------
class DeliveryStatus:
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED_OPTOUT = "suppressed_optout"
    SUPPRESSED_UNREACHABLE = "suppressed_unreachable"
    CAPPED = "capped"                # blocked by frequency cap / dedup (M3)
    HELDOUT_CONTROL = "heldout_control"  # held out as control group (M3)


@dataclass
class DeliveryRecord:
    """One user-level touch outcome. Shared log schema across M1/M3/M4.

    Fields mirror the survey's required touch-log columns
    (user_id, campaign_id, channel, time, content_id, status, click, convert).
    """
    customer_id: str
    campaign_id: str
    channel: str
    content_id: str
    ts: datetime
    status: str
    variant: str = "default"
    clicked: bool = False
    converted: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_sent(self) -> bool:
        return self.status == DeliveryStatus.SENT


# --- messaging gateway contract (implemented by M1, consumed by M3) -----------
@runtime_checkable
class MessagingGateway(Protocol):
    def send_batch(
        self,
        customer_ids: List[str],
        channel: str,
        content_id: str,
        *,
        campaign_id: str,
        dataset: Dict[str, Any],
        now: datetime,
        variant: str = "default",
    ) -> List[DeliveryRecord]:
        """Attempt to deliver `content_id` to each user; return one record per user."""
        ...


# --- deterministic bucketing (stable A/B split, control hold-out, sampling) ---
def stable_fraction(*parts: Any) -> float:
    """Return a stable float in [0, 1) for the given key parts.

    Deterministic across processes/runs (unlike hash()), so a user always lands
    in the same A/B variant / control bucket.
    """
    key = "::".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    # take first 8 bytes as an unsigned int, normalize to [0, 1)
    n = int.from_bytes(digest[:8], "big")
    return n / float(1 << 64)


def stable_bucket(key: Any, buckets: int, *, salt: str = "") -> int:
    """Map `key` to an integer bucket in [0, buckets)."""
    if buckets <= 0:
        raise ValueError("buckets must be positive")
    return int(stable_fraction(salt, key) * buckets)


__all__ = [
    "Channel",
    "DeliveryStatus",
    "DeliveryRecord",
    "MessagingGateway",
    "stable_fraction",
    "stable_bucket",
]
