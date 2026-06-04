# Growth Platform · Work Handover Checklist (Handover)

> Handover date: 2026-06-04 ｜ Repository: `https://github.com/faye-rao/Growth` (default branch main)
> Local: `C:\Faye\Growth\botim-growth-m2-cohort` (code) ＋ `C:\Faye\Growth\*.md` (analysis documents)
> Companion docs: `Growth-实现对比报告.md` (per-feature completeness), `ARCHITECTURE.md` (architecture), `Growth特性清单-M*-1.md` (requirements), `Growth技术方案-*.md` (technical selection), `Growth-requirement-prompt.md` (requirement prompt record)

---

## A. Project Background (30 seconds)
Build an in-house **user growth platform** for Botim (Dubai, launched in UAE, target users ≈ 2.5M), replacing the competitor MoEngage. Scope and priorities come from the interview survey (`用增问题survey-updated v3.xlsx`). All 9 modules M1–M9 have been built into **runnable, testable MVPs**, decomposed by functional independence into 7 services + 1 API gateway, with CI integrated.

---

## B. Completed Work

### B1. Code and Tests (repository faye-rao/Growth)
- **9 business modules** (`src/`, Python, zero core dependencies):
  - `cohort_engine`(M2), `messaging`(M1), `orchestration`(M3), `analytics`(M4), `personalization`(M5), `copywriting`(M6), `shadow`(M7), `data_foundation`(M8), `behavioral`(M9)
- **Shared contract** `growth_common` (DeliveryRecord messaging-log schema, MessagingGateway protocol, deterministic bucketing stable_fraction)
- **7 services** (`src/services/`, each an independent FastAPI app, independently deployable): data-platform / audience / personalization / campaign / content / analytics / experiment
- **API gateway** `src/api_gateway.py`: prefix routing + MOE-APPKEY authentication (401) + per-key token-bucket rate limiting (429) + /health
- **End-to-end**: `examples/e2e_demo.py` (cohort segmentation → orchestration → messaging execution → personalization → Shadow → funnel) + `tests/test_integration_e2e.py`
- **Tests: 269 all passing** (17 test files, covering each module + services/gateway + e2e)
- **CI**: `.github/workflows/ci.yml`, triggered on push/PR, runs pytest on py3.10/3.11/3.12
- **Git history**: per-module semantic commits (feat(M1)…feat(M9), feat(common), feat(services), ci, docs, test(e2e))

### B2. Differentiating Highlights Already Delivered (relative to MoEngage)
- **Cross-product funnel** (M4, which MoEngage cannot answer): Call→Wallet→Remittance, service penetration KPI 7.5%→15%
- **Three-solution cohort segmentation engine** (M2): interpreted execution + compiled SQL + RoaringBitmap (sub-second union/intersection/difference at 2.5M scale)
- **NL2SQL natural-language cohort segmentation** (M2, deterministic template version, breaking the "hard to use" problem)
- **Cross-campaign frequency capping/dedup** (M3, a gap in the current state of MoEngage/Botim)
- **Shadow non-inferiority validation gate** (M7, CI confidence interval + dedup to prevent double-sending)
- **Multilingual AI copywriting + compliance pre-screening** (M6, en/ar/hi/tl, disclaimers preserved across truncation)
- **In-house RFM/churn/engagement** (M9, replacing MoEngage internal metrics to avoid supply cutoff)

### B3. Documentation (`C:\Faye\Growth\`)
- Requirements: `Growth特性清单-M1-1.md`…`M9-1.md` + `Growth特性清单-总览索引.md` (Chinese) / `Growth-Feature-List-M1.md`…`M9.md` (English)
- Technical solutions: `Growth技术方案-M1-M3/M4-M6/M7-M9.md` (Chinese) + `Growth-Tech-Solutions-*.md` (English)
- Comprehensive analysis: `Botim增长平台_基于Survey的重新分析.md`, `MoEngage特性清单_按菜单维度.md`, `MoEngage视频特性拆解_前端后端数据.md`
- Architecture: `ARCHITECTURE.md` (in repository)
- This handover: `Growth-实现对比报告.md`, `Growth-交接清单.md`, `Growth-requirement-prompt.md`

### B4. Completeness Snapshot (see comparison report for details)
M1~60% · M2~65% · M3~50% · M4~80% · M5~60% · M6~65% · M7~55% · M8~65% · M9~60% ｜ **average ~62%** (feature-list coverage; infrastructure scaffolding all built)

---

## C. Remaining Work Checklist

### C0. 🔴 Immediately Actionable (handover day)
- [ ] **Verify CI is green**: after logging in, check the three-tier Python test results on the repository Actions page (our `gh` is not logged in and cannot read them)
- [ ] **Run services locally for self-test**: `pip install -e ".[dev]" && pytest`; after `uvicorn api_gateway:app`, walk through the gateway routes
- [ ] Incorporate analysis documents such as `Growth-requirement-prompt.md` (already redacted) into the repository docs/ as needed

### C1. 🟥 P0 Production Infrastructure (the biggest gap from MVP to launchable)
- [ ] **Persistence and real data ingestion**: footprint event ingestion (Kafka/batch), wide tables persisted to OLAP (Data Team to decide ClickHouse/Doris/StarRocks), messaging/conversion logs persisted to storage (M8 is currently an in-memory contract)
- [ ] **M2 compiled SQL connected to real OLAP**: `sql_compiler` already produces SQL; needs to connect to an engine for execution + batch-run scheduling for large cohorts (A5/A8)
- [ ] **M5 personalization hot path**: pre-computed cohorts + Redis point lookups + cache fallback (currently real-time hits at request time, with QPS/latency below target); add **authentication (AppKey)**, **scheduling + time zone (Asia/Dubai)**, active/ended publish states, conversion goals
- [ ] **M1 send pipeline**: Kafka peak-shaving queue to carry million-scale volume, integrate with Botim open platform's real rate-limit interface, persist messaging logs to storage
- [ ] **Unify time zone Asia/Dubai**: M3/M5 currently use naive datetime; scheduling/quiet hours/attribution must be unified to the UAE standard
- [ ] **Authentication and multi-tenancy**: the gateway has MOE-APPKEY, but module-level authentication, token system, and auditing are still to be added

### C2. 🟧 P1 Feature Completion (by module)
- [ ] **M3 orchestration** (largest gap): campaign state machine (draft/published/running/paused/ended), Flow nodes (delay/branch/wait-for-event/webhook), one-click campaign-level template reuse, quiet hours, A/B/N significance winner feedback (test code already in M7), front-end orchestration UI
- [ ] **M3↔M6 integration**: inject M6-generated copy into M3's A/B/N variants (currently not connected)
- [ ] **M1 In-App**: campaign-slot/page-position configuration model, page-level frequency capping (first time / first time per page / first time per day), SDK self-rendering delivery protocol
- [ ] **M7 Shadow**: MoEngage messaging stream ingestion (group D, requires vendor cooperation), reuse M4 attribution standard (C4), configurable observation window + sequential test early stopping, CUPED variance reduction
- [ ] **M4**: cross-product funnel SQL-ification, reconciliation discrepancy alert thresholds, ROI metrics
- [ ] **M8**: lightweight Kafka subscription feeding the suppression layer, DQC data-drift detection, Mapping accuracy verification, tag dictionary/coverage
- [ ] **M9**: align with Growth on a list of "5–10 reports people actually look at" and reproduce them (proving the numbers match), report export (PDF/visualization), per-dimension anomaly attribution

### C3. 🟨 P2 AI Incremental Main Line (the survey positions "incremental value comes from AI"; currently almost entirely stubs)
- [ ] **Real LLM integration**: M6 copywriting (`CopyProvider` protocol already reserved; swap in a real LLM provider), M2 NL2SQL (template → RAG + schema-linking + LLM, keeping the template as fallback)
- [ ] **M3 AI orchestration** (the biggest highlight called out by the survey): natural language → cohort + copy + scheduling + Flow, end-to-end
- [ ] **M2 intelligent segmentation**: Lookalike similarity expansion, churn/conversion propensity scoring, AI segmentation suggestions, segmentation-effectiveness algorithm optimization (all 4 items in the C series are blank)
- [ ] **M1 delivery optimization**: reachability prediction scoring/ranking, best send time STO, Next-Best-Channel
- [ ] **M6 effectiveness learning**: copy↔effectiveness library, high-conversion style learning, real bandit/online learning
- [ ] **M9 narrative BI**: generative insights, NL data querying (text-to-SQL)

### C4. 🟩 Engineering and Launch
- [ ] Containerization (Dockerfile/compose), independent per-service deployment and K8s/orchestration
- [ ] Observability (structured logging, metrics, distributed tracing, alerting)
- [ ] OpenAPI contract + contract testing, load/stress testing (especially the M5 fetch hot path, M2 2.5M-cohort batch runs)
- [ ] Security review (authentication, PII, rate limiting, compliance — UAE Fintech)

---

## D. Key Dependencies & Blockers (require external coordination)
| Owner | To be provided (determines whether work can proceed) | Blocked work |
|---|---|---|
| **Data Team (Mr. Ma)** | OLAP selection decision, ER diagram/database tables, ID-Mapping table + coverage, T+1 cleaning, redacted samples, historical query SQL distribution (to evaluate NL2SQL) | All of C1, M2/M8, NL2SQL |
| **Growth (Dubai, Radhika)** | Top Cohort definition, list of reports people actually look at, Flow node types/complexity, frequency policy, Shadow scenarios and acceptance criteria | M2/M3/M4/M7/M9 feature finalization |
| **Pei Qing** | Event schema, data samples, arrange Dubai shadowing | M8 integration, overall kickoff |
| **MoEngage vendor** | Messaging stream ingestion method/latency (D23), hidden Webhook/Connector | M7 Shadow comparison |

> ⚠️ Most of these are still in the "open/to be confirmed" state in the survey — **prioritize closing out these interviews before kickoff** (Plan W1–W2). Estimates and plans carry a ±30% range until the data/answers are in place.

---

## E. Onboarding Guide (5 steps for new colleagues)
1. `git clone https://github.com/faye-rao/Growth && cd Growth`
2. `python -m pip install -e ".[dev]"` → `pytest` (should be 269 passing)
3. Read `ARCHITECTURE.md` (full picture of 7 services + gateway) → `README.md` (M2 details + overview of each module)
4. Run `python examples/e2e_demo.py` to see the end-to-end path; `uvicorn api_gateway:app` + `/health` to see service routing
5. Read `src/<pkg>/` per module + the corresponding `tests/test_<pkg>.py`; cross-reference `Growth-实现对比报告.md` to see each module's "done/gaps", and pick up a task from section C to own

## F. Risks
- **Over-trusting the MVP**: this is currently an algorithm/contract MVP, **not a production system** — no persistence, no real data source, no real LLM; do not point real traffic at it directly.
- **Number credibility**: the prerequisite for replacing MoEngage is "the numbers match" (emphasized by the survey); the M4/M9 reports must be dual-run and reconciled against the old system before operations will trust them.
- **Unstandardized definitions**: conversion/active/retention have no company-wide unified definition (D29); attribution must align on definitions before development, otherwise rework.
- **Shadow double-send**: before going live with real Shadow, the M7 dedup middle layer must connect to both real send channels, otherwise the comparison is distorted.
