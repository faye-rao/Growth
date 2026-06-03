"""Scale benchmark: bitmap audience-size estimation at UAE scale (~2.5M users).

Streams synthetic users directly into the inverted index (so we never hold 2.5M
dicts in memory), then times audience-size estimation for several cohorts.

    python examples/benchmark.py [N]      # N defaults to 2_500_000
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cohort_engine.bitmap_engine import BitmapIndex
from cohort_engine.parser import parse_segment

COUNTRIES = ["AE", "IN", "PH", "PK", "EG", "BD", "NP"]
PLATFORMS = ["Android", "iOS"]
BALANCE_BUCKETS = [i * 500 for i in range(0, 21)]  # 0..10000, bounded distinct values

SPECS = {
    "KYC & balance>=1000 & wallet not activated": {"match": {"op": "and", "children": [
        {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
        {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
    ]}},
    "country in [AE]": {"match": {"type": "attribute", "field": "country", "operator": "in", "value": ["AE"]}},
    "balance between [1000,6000]": {"match": {"type": "attribute", "field": "balance", "operator": "between", "value": [1000, 6000]}},
    "NOT kyc": {"match": {"op": "not", "children": [{"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}]}},
    "dormant tag (event-derived)": {"match": {"type": "attribute", "field": "dormant", "operator": "eq", "value": True}},
}


def build_index(n: int, seed: int = 42) -> BitmapIndex:
    rng = random.Random(seed)
    idx = BitmapIndex()
    for ordinal in range(n):
        record = {
            "country": rng.choice(COUNTRIES),
            "platform": rng.choice(PLATFORMS),
            "is_kyc": rng.random() < 0.6,
            "wallet_activated": rng.random() < 0.35,
            "balance": rng.choice(BALANCE_BUCKETS),
            "dormant": rng.random() < 0.2,  # pre-computed event-derived boolean tag
        }
        idx.add(ordinal, record)  # no customer_id -> size-only benchmark
    idx.finalize()
    return idx


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2_500_000
    print(f"Building inverted index for N = {n:,} users ...")
    t0 = time.perf_counter()
    idx = build_index(n)
    build_s = time.perf_counter() - t0
    print(f"  index built in {build_s:.2f}s  (distinct balance values: {len(idx.attr['balance'])})\n")

    print(f"{'cohort':<46}{'size':>12}{'latency':>14}")
    print("-" * 72)
    for label, spec in SPECS.items():
        seg = parse_segment(spec)
        t0 = time.perf_counter()
        size = len(idx.segment_bitmap(seg))
        ms = (time.perf_counter() - t0) * 1000
        print(f"{label:<46}{size:>12,}{ms:>11.2f} ms")

    print("\nNote: audience-size estimation is bitmap cardinality -> sub-second at 2.5M,")
    print("vs. O(users x events) per-user scan in the in-memory evaluator.")


if __name__ == "__main__":
    main()
