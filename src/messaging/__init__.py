"""Botim Growth Platform — M1 Messaging Execution (MVP).

Unified messaging gateway (the recommended "gateway收口" design): a single
``Gateway`` that all campaigns send through, so suppression, reachability,
rate-limiting and multi-channel fallback live in one place instead of being
re-implemented per channel.

Public API::

    from messaging import Gateway, RateLimiter
    from messaging.sample_data import build_messaging_dataset, OPT_OUT, NOW

    gw = Gateway(opt_out=OPT_OUT, rate_limiter=RateLimiter(capacity=100))
    records = gw.send_batch(
        ["u1", "u2"], channel="push", content_id="welcome",
        campaign_id="c1", dataset=build_messaging_dataset(), now=NOW,
    )

``Gateway`` implements the shared ``MessagingGateway`` protocol from
``growth_common`` so M3 (orchestration) can drive it. Zero third-party deps.
"""
from .adapters import ChannelAdapter, PushAdapter, SmsAdapter, InAppAdapter
from .rate_limiter import RateLimiter
from .gateway import Gateway

__all__ = [
    "Gateway",
    "RateLimiter",
    "ChannelAdapter",
    "PushAdapter",
    "SmsAdapter",
    "InAppAdapter",
]
__version__ = "0.1.0"
