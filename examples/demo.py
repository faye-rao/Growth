"""Runnable demo: three realistic Botim cohorts -> matched IDs, size, and SQL.

    python examples/demo.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cohort_engine import CohortEngine
from cohort_engine.sample_data import NOW, build_sample_dataset

COHORTS = {
    "高价值未激活钱包 (high-value, wallet not activated)": {
        "match": {"op": "and", "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
            {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
        ]},
    },
    "频繁登出+设备异常 (logout predominantly on device_height=5, last 3d)": {
        "match": {"type": "event", "event": "User Logout", "frequency": {"op": "predominantly"},
                  "within_days": 3, "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}},
    },
    "KYC 用户但 90 天未转账 (KYC but no transfer in 90d)": {
        "match": {"op": "and", "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"op": "not", "children": [
                {"type": "event", "event": "Transfer", "frequency": {"op": "at_least", "value": 1}, "within_days": 90},
            ]},
        ]},
    },
}


def main():
    engine = CohortEngine(build_sample_dataset(), now=NOW)
    print(f"reference now = {NOW.isoformat()}\n" + "=" * 72)
    for title, spec in COHORTS.items():
        ids = sorted(engine.evaluate(spec))
        size = engine.estimate_size(spec)
        sql = engine.compile_sql(spec)
        print(f"\n### {title}")
        print(f"  DSL      : {json.dumps(spec['match'], ensure_ascii=False)}")
        print(f"  matched  : {ids}")
        print(f"  size est : {size}")
        print(f"  SQL      : {sql}")


if __name__ == "__main__":
    main()
