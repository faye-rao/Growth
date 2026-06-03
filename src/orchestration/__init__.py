"""Botim Growth Platform — M3 Content & Push Orchestration (MVP).

Step ② of the MoEngage-style campaign flow (M2 segments the audience, M3
orchestrates delivery): deterministic A/B/n variant allocation, control
hold-out, frequency capping / cross-campaign dedup, and batch vs.
event-triggered campaign execution over the shared ``MessagingGateway``.

Public API::

    from orchestration import Campaign, Variant, Schedule
    from orchestration import CampaignRunner, FrequencyCapper, allocate

    campaign = Campaign(
        id="c1", audience_spec=rule_dsl, channel="push",
        variants=[Variant("A", 1, "welcome_a"), Variant("B", 1, "welcome_b")],
        control_pct=0.1,
        schedule=Schedule(start, end, trigger_type="batch"),
    )
    runner = CampaignRunner(engine=cohort_engine, gateway=gateway)
    result = runner.run(campaign, dataset, now)

Zero third-party dependencies (stdlib + the shared ``growth_common`` contract).
"""
from .allocator import CONTROL, allocate, assign
from .frequency import CapResult, FrequencyCapper
from .models import BATCH, TRIGGERED, Campaign, Schedule, Variant
from .runner import CampaignRunner, RunResult

__all__ = [
    "Variant",
    "Schedule",
    "Campaign",
    "BATCH",
    "TRIGGERED",
    "allocate",
    "assign",
    "CONTROL",
    "FrequencyCapper",
    "CapResult",
    "CampaignRunner",
    "RunResult",
]
__version__ = "0.1.0"
