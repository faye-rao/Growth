# Botim Growth Platform — Test Report

> Repository: `https://github.com/faye-rao/Growth` ｜ Generated: 2026-06-04
> Result: **269 passed, 0 failed** ｜ Coverage: **90%** (src/) ｜ 1 non-fatal warning
> Environment: Python 3.11.9, pytest + pytest-cov; CI runs the same suite on Python 3.10 / 3.11 / 3.12.

---

## 1. Where to see test results

Test **results** are not files committed to the repo — only the **test cases**
(`tests/test_*.py`) are. Results are produced by *running* the suite:

- **In CI (GitHub):** every push / PR to `main` triggers the `CI` workflow
  (`.github/workflows/ci.yml`). Open the repo's **Actions** tab → pick a run →
  each Python-version job shows pass/fail in its logs. The run's **Summary** page
  now also prints the pytest summary, and **JUnit XML + coverage XML** are attached
  as downloadable **Artifacts** (`test-results-py3.xx`).
- **Locally:**
  ```bash
  pip install -e ".[dev]"
  pytest -q                         # 269 passed
  pytest --cov=src --cov-report=term-missing   # with coverage
  ```

---

## 2. Summary

| Metric | Value |
|---|---|
| Total tests | **269** |
| Passed | 269 |
| Failed / Errored | 0 |
| Warnings | 1 (pre-existing Starlette/httpx `TestClient` deprecation — non-fatal) |
| Line coverage (src/) | **90%** (2569 stmts, 251 missed) |
| Test files | 19 |
| Python versions (CI) | 3.10, 3.11, 3.12 |

---

## 3. Results by test suite

| Test file | Tests | Module / Area |
|---|---:|---|
| test_evaluator.py | 22 | M2 Cohort rule evaluation |
| test_parser.py | 12 | M2 DSL parsing/validation |
| test_sql_compiler.py | 8 | M2 compile-to-SQL |
| test_engine.py | 5 | M2 engine facade |
| test_nl2sql.py | 13 | M2 NL2SQL |
| test_templates.py | 7 | M2 cohort templates |
| test_bitmap_engine.py | 13 | M2 RoaringBitmap audience engine |
| test_api.py | 10 | M2 REST API |
| test_review_fixes.py | 5 | M2 review-regression locks |
| test_messaging.py | 14 | M1 Messaging Execution |
| test_orchestration.py | 13 | M3 Orchestration (A/B/N, freq cap) |
| test_analytics.py | 13 | M4 Funnel / attribution / cross-product |
| test_personalization.py | 21 | M5 Personalization (fetch) |
| test_copywriting.py | 28 | M6 AI Copywriting |
| test_shadow.py | 24 | M7 Shadow Validation |
| test_data_foundation.py | 15 | M8 Data Foundation |
| test_behavioral.py | 22 | M9 Behavioral Analytics |
| test_services_gateway.py | 15 | 7 services + API gateway |
| test_integration_e2e.py | 9 | End-to-end pipeline |
| **Total** | **269** | |

---

## 4. Coverage by module (line %)

| Package (module) | Coverage |
|---|---:|
| shadow (M7) — report 100%, splitter 100%, dedup 96% | **~99%** |
| cohort_engine (M2) — sample_data/templates 100%, sql_compiler 86% | **~92%** |
| messaging (M1) — gateway 98%, adapters 95%, rate_limiter 82% | **~94%** |
| orchestration (M3) — runner 97%, allocator 96%, frequency 81%, models 83% | **~89%** |
| personalization (M5) — service 97%, store 96%, models 94% | **~95%** |
| copywriting (M6) — feedback 97%, generator 95%, models 91%, provider 90%, compliance 89% | **~92%** |
| data_foundation (M8) — warehouse 100%, id_mapping/ingestion 94%, dqc 91%, suppression 83% | **~92%** |
| analytics (M4) | high (covered via analytics + behavioral suites) |
| behavioral (M9) | high |
| growth_common (shared) | 93% |
| services/ (7 service apps) | 49–81% (thin wrappers; exercised via gateway tests; lower lines are error-branch/uncalled endpoints) |
| **TOTAL (src/)** | **90%** |

> Note: the lowest-covered files are the FastAPI **service wrappers** (`services/*.py`,
> 49–81%) — thin adapters whose un-covered lines are mostly alternate endpoints /
> error branches not hit by the representative gateway tests. Core business logic
> (rule engine, funnel, shadow stats, frequency capping, dedup) is ≥90%.

---

## 5. Notable correctness coverage (regression-locked bugs)

These real bugs were found in independent Code Review and are now covered by
dedicated regression tests:

| Module | Bug fixed | Test |
|---|---|---|
| M3 | run accounting under-counted gateway-suppressed sends | `test_orchestration.py::test_accounting_balances_with_suppressing_gateway` |
| M7 | non-inferiority verdict used wrong (pooled, two-sided) statistics | `test_shadow.py` (CI-based verdict cases) |
| M8 | dedup wrongly collapsed distinct same-second events | `test_data_foundation.py::test_ingest_keeps_distinct_events_sharing_natural_key` |
| M6 | fintech disclaimer truncated away under channel length limit | `test_copywriting.py::test_disclaimer_survives_truncation_for_fintech_push` |
| M2 | NOT-group SQL parenthesization; malformed-ts parity | `test_review_fixes.py` |

---

## 6. End-to-end coverage

`test_integration_e2e.py` (9 tests) exercises the full chain across modules:
Data Foundation → Cohort Segmentation → AI Copy → Orchestration (A/B/N + control)
→ Messaging send → Personalization fetch → Shadow split/report → Funnel/attribution,
asserting cross-module consistency (audience flows through, delivery log balances,
funnel computes, shadow report has both arms).

---

## 7. Scope note — backend only, no frontend

This suite covers **backend** logic only (Python modules, FastAPI services, gateway).
**No frontend/UI has been designed or implemented** — items such as the visual rule
builder (M2-A6), orchestration UI (M3-G1), and the personalization 3-step wizard
(M5-F1/F2/F3) are listed in the feature lists but marked **⬜ Not implemented** in
`Growth-Implementation-Audit.md`. There are therefore no UI/e2e-browser tests.

---

## 8. How to reproduce

```bash
git clone https://github.com/faye-rao/Growth && cd Growth
python -m pip install -e ".[dev]"
pytest -q                                   # -> 269 passed
pytest --cov=src --cov-report=term-missing  # -> TOTAL 90%
python examples/e2e_demo.py                 # end-to-end demo
uvicorn api_gateway:app --reload            # gateway + mounted services
```
