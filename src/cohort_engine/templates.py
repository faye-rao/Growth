"""High-frequency Cohort template library (M2-D2).

Per the survey, ~80% of campaigns use only 5–10 segments (KYC / last-transfer /
wallet-activation / balance). These parametrized templates make those one-click
reusable and guarantee a consistent, reviewed rule shape.

Each template returns a rule spec dict ({"name": ..., "match": ...}) ready for
CohortEngine.evaluate / compile_sql.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List


def high_value_wallet_inactive(min_balance: float = 1000) -> Dict[str, Any]:
    """KYC users with balance >= min_balance who have NOT activated the wallet."""
    return {
        "name": f"high_value_wallet_inactive(min_balance={min_balance})",
        "match": {"op": "and", "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"type": "attribute", "field": "balance", "operator": "gte", "value": min_balance},
            {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
        ]},
    }


def kyc_no_transfer(days: int = 90) -> Dict[str, Any]:
    """KYC users with no Transfer in the last `days` days (cross-sell candidates)."""
    return {
        "name": f"kyc_no_transfer(days={days})",
        "match": {"op": "and", "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"op": "not", "children": [
                {"type": "event", "event": "Transfer",
                 "frequency": {"op": "at_least", "value": 1}, "within_days": days},
            ]},
        ]},
    }


def dormant_users(event: str = "App Opened", days: int = 30) -> Dict[str, Any]:
    """Users who have NOT fired `event` in the last `days` days (re-activation)."""
    return {
        "name": f"dormant_users(event={event!r}, days={days})",
        "match": {"op": "not", "children": [
            {"type": "event", "event": event,
             "frequency": {"op": "at_least", "value": 1}, "within_days": days},
        ]},
    }


def country_segment(codes: List[str]) -> Dict[str, Any]:
    """Users in the given country codes."""
    return {
        "name": f"country_segment({codes})",
        "match": {"type": "attribute", "field": "country", "operator": "in", "value": list(codes)},
    }


def frequent_event(event: str, times: int = 3, days: int = 7) -> Dict[str, Any]:
    """Users who fired `event` at least `times` times in the last `days` days."""
    return {
        "name": f"frequent_event(event={event!r}, times={times}, days={days})",
        "match": {"type": "event", "event": event,
                  "frequency": {"op": "at_least", "value": times}, "within_days": days},
    }


# registry for discovery / API listing
TEMPLATES: Dict[str, Callable[..., Dict[str, Any]]] = {
    "high_value_wallet_inactive": high_value_wallet_inactive,
    "kyc_no_transfer": kyc_no_transfer,
    "dormant_users": dormant_users,
    "country_segment": country_segment,
    "frequent_event": frequent_event,
}


def build(name: str, **params: Any) -> Dict[str, Any]:
    """Instantiate a template by name with parameters."""
    if name not in TEMPLATES:
        raise KeyError(f"unknown template '{name}'; available: {sorted(TEMPLATES)}")
    return TEMPLATES[name](**params)
