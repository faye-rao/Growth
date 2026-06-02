# Botim Growth Platform — M2 Cohort Segmentation Rule Engine (MVP)

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

## Project layout

```
src/cohort_engine/   models · parser · evaluator · sql_compiler · engine · sample_data
tests/               parser · evaluator · sql_compiler · engine
examples/demo.py     runnable showcase
TEST_CASES.md        test-case design (feature → test mapping)
```
