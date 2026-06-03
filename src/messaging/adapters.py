"""Channel adapters — the per-channel "last mile" senders.

Each adapter exposes ``deliver(customer_id, content_id, user) -> bool`` where the
return value means *accepted by the downstream provider* (True) vs *rejected*
(False). Outcomes are deterministic so tests can assert them.

Design note (the "MoEngage has no direct push right" constraint): MoEngage can
trigger SMS / in-app surfaces, but it cannot self-send Botim push. So the push
adapter routes to a stubbed **Botim push API** rather than a 3rd-party vendor.
"""
from __future__ import annotations

from typing import Any, Dict

from growth_common import Channel


class ChannelAdapter:
    """Base channel adapter. Subclasses implement :meth:`deliver`."""

    channel: str = ""

    def deliver(self, customer_id: str, content_id: str, user: Dict[str, Any]) -> bool:
        """Hand the message to the downstream provider. True == accepted."""
        raise NotImplementedError


class PushAdapter(ChannelAdapter):
    """Routes to the stubbed Botim self-send push API.

    Push is rejected deterministically when the user has no ``push_token``
    (nothing to address the device with).
    """

    channel = Channel.PUSH

    def deliver(self, customer_id: str, content_id: str, user: Dict[str, Any]) -> bool:
        return self._botim_push_api(customer_id, content_id, user)

    @staticmethod
    def _botim_push_api(customer_id: str, content_id: str, user: Dict[str, Any]) -> bool:
        # Stubbed Botim push backend: a missing/empty push_token can't be addressed.
        return bool(user.get("push_token"))


class SmsAdapter(ChannelAdapter):
    """SMS fallback — accepted when the user has a phone number."""

    channel = Channel.SMS

    def deliver(self, customer_id: str, content_id: str, user: Dict[str, Any]) -> bool:
        return bool(user.get("phone"))


class InAppAdapter(ChannelAdapter):
    """In-app surface — always accepted (rendered on next app open)."""

    channel = Channel.IN_APP

    def deliver(self, customer_id: str, content_id: str, user: Dict[str, Any]) -> bool:
        return True
