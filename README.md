# Botim Growth Platform — M2 Cohort Segmentation Rule Engine (MVP)

[![CI](https://github.com/faye-rao/Growth/actions/workflows/ci.yml/badge.svg)](https://github.com/faye-rao/Growth/actions/workflows/ci.yml)

A self-built replacement for MoEngage's audience-segmentation rule engine
(step ① of MoEngage's 3-step campaign flow). This MVP implements the **core rule
engine** (features **M2-A1 ~ A6** in the M2 feature list):

- **M2-A1** Nested `AND` / `OR` / `NOT` rule composition (arbitrary depth)
- **M2-A2** Time-window operator (`within_days` / last N days)
- **M2-A3** Attribute operators (`eq/ne/gt/gte/lt/lte/in/not_in/exists/not_exists/between/contains`)
  and frequency operators (`at_least/at_most/exactly/min_percent/predominantly`)
- **M2-A4** Exclude-users sub-tree
- **M2-A5** Batch evaluation → set of `customer_id`
- **M2-A6** Real-time audience-size estimation
- **M2-A7** JSON DSL parser/validator (the MoEngage-syntax-compatible entry layer)
- **Solution B** Compile-to-SQL (DSL → ANSI-ish SQL for OLAP push-down)

> Out of scope for this MVP (tracked in the M2 feature list): NL2SQL (B-series),
> Lookalike / propensity (C-series), Bitmap audience algebra, near-real-time refresh.

## Platform modules

This repo is a monorepo for the Botim Growth Platform. Modules share contracts via
`growth_common` (delivery-record schema, `MessagingGateway` protocol, deterministic
bucketing) and interoperate:

| Pkg | Module | What it does |
|---|---|---|
| `cohort_engine` | **M2** Segmentation | rule engine + NL2SQL + templates + bitmap + SQL/REST |
| `messaging` | **M1** Messaging Execution | unified gateway: opt-out → reachability → rate-limit → channel fallback; user-level delivery log |
| `orchestration` | **M3** Orchestration | campaigns: deterministic A/B/N split + control hold-out + frequency cap / cross-campaign dedup; batch vs triggered |
| `analytics` | **M4** Funnel Tracking | ordered funnel, attribution (first/last touch within window), **cross-product funnel** |
| `personalization` | **M5** 1-to-1 Personalization | `experiences/fetch`-style: audience hit + variation + **publish gating** + multi-language payload (app self-renders) |
| `shadow` | **M7** Shadow Validation | traffic split + **dedup (no double-send)** + non-inferiority A/B gate (CI-based) |

`M3` resolves audiences via `M2` and sends via the `M1` gateway; `M5` decides home-card
content for the same cohorts; `M7` gates the rollout; `M4` consumes the delivery log
emitted by `M1`/`M3`. See the full pipeline wired together in
[`examples/e2e_demo.py`](examples/e2e_demo.py) (covered by `tests/test_integration_e2e.py`):

```
M2 segment → M3 orchestrate (A/B + control + freq-cap) → M1 deliver
M5 personalize (home-card) │ M7 shadow-validate (gate) │ M4 funnel + attribution
```

## Architecture

```
JSON DSL ──parser.py──► Segment AST ──┬── evaluator.py  (in-memory, batch)   → matched IDs / size
                                      └── sql_compiler.py (compile-to-SQL)    → SQL for OLAP
                          engine.py = CohortEngine facade over both
```

Zero third-party runtime dependencies (stdlib only). `pytest` for tests.

## Quick start

```bash
python -m pip install -e ".[dev]"   # or: pip install pytest
pytest                              # run the test suite
python examples/demo.py             # see 3 realistic cohorts evaluated
```

## Rule DSL example

```json
{
  "name": "high-value, wallet not activated",
  "match": {
    "op": "and",
    "children": [
      {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": true},
      {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
      {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": false}
    ]
  }
}
```

Event condition with frequency + time-window + event-property filter:

```json
{
  "type": "event",
  "event": "User Logout",
  "frequency": {"op": "predominantly"},
  "within_days": 3,
  "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5}
}
```

## Frequency semantics

Given the window-filtered occurrences of an event (`within_days`), and `matching`
= occurrences that also satisfy `where` (or all occurrences if no `where`):

| op | meaning |
|---|---|
| `at_least` / `at_most` / `exactly` N | `len(matching)` compared to N |
| `min_percent` X | `total>0` and `matching/total*100 ≥ X` |
| `predominantly` | `total>0` and `matching/total > 0.5` |

## NL2SQL (M2-B): natural-language → cohort

Deterministic template/slot translator (no external LLM) — predictable accuracy on
high-frequency phrasings, confidence score, and human-review fallback:

```python
from cohort_engine import CohortEngine
from cohort_engine.nl2sql import translate

res = translate("KYC users with balance over 1000 and wallet not activated")
res.dsl              # {"match": {...}}  -> previewable / editable (B2)
res.confidence       # 1.0               -> matched_clauses / total (B3)
res.requires_review  # False
CohortEngine(...).evaluate(res.dsl)      # -> {"u1", "u4"}
```

Supported grammar (canonical phrasings): `KYC/verified users`, `wallet (not) activated`,
`android/ios users`, `balance over/under/at least N`, `(users) in <COUNTRY|CC>`,
`(have not) logged out / transferred / opened app [at least N times] [in the last M days]`,
joined by `and` / `or`. Unrecognized clauses lower the confidence and are returned in
`unmatched` for human review.

## Cohort template library (M2-D2)

```python
from cohort_engine import templates as T
T.high_value_wallet_inactive(min_balance=1000)
T.kyc_no_transfer(days=90)
T.dormant_users(event="App Opened", days=30)
T.build("country_segment", codes=["AE"])     # by name
```

## REST API (optional `api` extra)

```bash
pip install -e ".[api]"
uvicorn cohort_engine.api:app --reload
```

| Method & path | Purpose |
|---|---|
| `POST /segments/evaluate` | matched customer_ids + size |
| `POST /segments/size` | audience-size estimate (M2-A6) |
| `POST /segments/compile` | equivalent SQL |
| `POST /nl2sql` | natural language → DSL + confidence |
| `GET  /templates` / `POST /templates/{name}` | list / run cohort templates |

## Scale: RoaringBitmap engine (M2 solution C)

Botim launches in the UAE at **~2.5M users** (≈ ¼ of the population). At that
scale the per-user evaluator can't answer audience-size queries interactively, so
the bitmap engine pre-indexes users into an inverted index of RoaringBitmaps;
audience algebra is bitmap AND/OR/ANDNOT and **size = bitmap cardinality**.

```bash
pip install -e ".[bitmap]"
python examples/benchmark.py 2500000
```

Measured on 2.5M synthetic users (single machine):

| cohort | size | latency |
|---|---:|---:|
| KYC & balance≥1000 & wallet not activated | 881,496 | **2.84 ms** |
| country in [AE] | 357,217 | **0.04 ms** |
| balance between [1000,6000] | 1,309,207 | **1.31 ms** |
| NOT kyc | 1,000,727 | **0.44 ms** |
| dormant tag (event-derived) | 500,310 | **0.06 ms** |

(index build ~9s). Event frequency/time-window conditions are pre-computed at T+1
into boolean tags (e.g. `dormant`) and indexed as attributes; conditions the index
can't serve raise `BitmapUnsupported` to fall back to the compile-to-SQL path.

```python
from cohort_engine.bitmap_engine import BitmapAudienceEngine
eng = BitmapAudienceEngine(dataset, tag_fns={"logout_anomaly": my_fn}, now=NOW)
eng.estimate_size(spec)   # bitmap cardinality, ms at millions of users
eng.evaluate(spec)        # set of customer_ids
```

## Project layout

```
src/cohort_engine/   models · parser · evaluator · sql_compiler · engine · sample_data
                     nl2sql (B) · templates (D2) · bitmap_engine (C) · api (FastAPI)
tests/               parser · evaluator · sql_compiler · engine · review_fixes
                     nl2sql · templates · bitmap_engine · api
examples/demo.py     runnable showcase   ·   examples/benchmark.py  2.5M-scale bench
TEST_CASES.md        test-case design (feature → test mapping)
```
