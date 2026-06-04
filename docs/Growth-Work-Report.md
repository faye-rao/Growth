# Growth Platform Project · Work Report and Work Process

> Reporter's perspective: the driver of requirements/solution/delivery for Botim's in-house user growth platform (replacing MoEngage)
> Period: 2026-06-02 ~ 2026-06-04 ｜ Delivery repository: `https://github.com/faye-rao/Growth`
> Related documents: `Growth-实现对比报告.md`, `Growth-交接清单.md`, `Growth-requirement-prompt.md`, `ARCHITECTURE.md`, `Growth特性清单-M*-1.md`, `Growth技术方案-*.md`

---

## 1. Project Overview

Build an in-house user growth platform for Botim (Dubai, launched in the UAE, target users ≈ 1/4 of the UAE population ≈ 2.5 million) to replace the competing product MoEngage. I drove the full process of **competitive research → requirements clarification → solution design → coding and delivery → validation → handover**. In the end, I built **all 9 modules (M1–M9) scoped by the survey into runnable, testable MVPs**, decomposed into **7 services + 1 API gateway** by functional independence, integrated CI, and produced a complete documentation system covering requirements/solution/comparison/handover.

**Work method**: frame-by-frame breakdown of competitor screen recordings + survey interview conclusions to drive scope → first produce the feature list and technical solution (including industry practices and AI increments) → deliver module by module with the discipline of TDD (test cases first) + independent Code Review + functional validation → contract-driven parallel development to speed things up → semantic commits to GitHub per module.

---

## 2. Work Process (9 Phases)

### Phase 1 · Environment Setup and Competitor Account Onboarding
- **Goal**: set up a competitor experience/scraping environment and access the actual MoEngage product.
- **Work**: configure Playwright MCP; log in to the MoEngage console (for security, credentials were entered by me personally and 2FA codes were handled by me); standardize login and scheduling conventions to **uniformly use the UAE time zone (Asia/Dubai, UTC+4)**.
- **Key Decisions**: credentials are not written into any file / not handed to automation (security red line); the time zone baseline is set to UAE (subsequently applied throughout scheduling/attribution/reporting).
- **Deliverables**: a usable competitor experience environment.

### Phase 2 · Competitor Video Breakdown and Feature List
- **Goal**: thoroughly understand the features from 2 MoEngage screen recordings (6'33" walkthrough + 4'03" Personalization hands-on).
- **Work**: extract frames and analyze screen by screen, broken down across the three layers of **frontend/backend/data**; then organize the feature list along menu dimensions such as **Segment / Campaigns / Dashboard / Analyze / Personalize**. Identify the most critical backend contract `POST /v1/experiences/fetch` (Personalization "borrow delivery, client self-renders").
- **Key Decisions**: confirm that the "homepage Personalization = in-house rule-based segmentation + delivery-only" path can be built in-house (lowest risk).
- **Deliverables**: `MoEngage视频特性拆解_前端后端数据.md`, `MoEngage特性清单_按菜单维度.md`.

### Phase 3 · Re-scoping Based on the Survey
- **Goal**: use real interview conclusions (`用增问题survey-updated v3.xlsx`, three sheets) to correct the "copy the competitor" scope.
- **Work**: read the survey/Plan/data-analysis specials and re-scope —— clarify that **we only do the 3 cores (Cohort Segmentation / Orchestration / Funnel Tracking) + Messaging Execution at the highest priority**, while **Dashboard/heavy BI are out of scope** (already covered by the Data Team + Amplitude), with increments coming from AI; map out modules, dependencies, effort, timeline, and organizational blockers.
- **Key Decisions**: cut Dashboard/full BI, downscale Analyze/Reports and merge them into Funnel Tracking; establish the pragmatic route of "6-week MVP + Shadow acceptance".
- **Deliverables**: `Botim增长平台_基于Survey的重新分析.md`.

### Phase 4 · Feature List Refinement and Technical Solution
- **Goal**: turn module requirements into a formal, handover-ready list + a decision-ready technical solution.
- **Work**: produce a **formal feature list** for each of M1–M9 (`Growth特性清单-M*-1.md`, annotated with 【Replica】/★ Enhancement/🤖AI + survey line-number traceability + cross-check completion + effort/dependency/risk); an overview index + cross-module dependency diagram + AI-highlight map; for each module produce **≥2 technical solution comparisons + typical industry practices + new AI approaches + a Botim-oriented selection**; and **translate the lists and technical solutions into English** for cross-team use.
- **Key Decisions**: establish the product narrative of "the replica guarantees no worse than the status quo, and AI delivers the increment"; clarify that OLAP selection is a shared prerequisite for multiple modules (pending the Data Team's decision).
- **Deliverables**: 9 Chinese lists + overview index + 3 technical solutions (CN/EN) + 9 English lists.

### Phase 5 · M2 Delivery (the first end-to-end engineering loop)
- **Goal**: deliver the cohort engine with the complete engineering discipline of "test cases → development → Code Review → functional validation → commit to GitHub".
- **Work**: TDD-design test cases → implement the rule engine DSL/parsing/evaluation/compile to SQL/headcount estimation → independent Code Review (fix SQL parenthesis, bad ts, etc.) → full validation → commit and push to `faye-rao/Growth`. Subsequently, based on the scale of **UAE ≈ 2.5 million users**, incrementally add a **RoaringBitmap cohort engine** (sub-second intersection/union/difference) + NL2SQL + a template library + REST API.
- **Key Decisions**: choose the Bitmap solution C based on user scale; for NL2SQL, first do deterministic templates + fallback (do not bet on full automation).
- **Deliverables**: `cohort_engine` module (multiple files) + 95 tests + CI prototype.

### Phase 6 · CI + M1/M3/M4 Delivery
- **Goal**: add CI; deliver Messaging/Orchestration/Funnel in parallel.
- **Work**: add GitHub Actions CI (py3.10–3.12); build a **shared contract `growth_common`** (unified messaging-log schema, gateway protocol, deterministic bucketing) so modules can **develop in parallel against the contract**; deliver M1 Messaging Execution, M3 Orchestration, and M4 Funnel in parallel; independent Code Review found and fixed the **M3 accounting non-conservation bug** (count omission when the gateway suppresses sending).
- **Key Decisions**: contract-driven parallel; dissolve module coupling with the shared contract.
- **Deliverables**: M1/M3/M4 modules + CI + test report.

### Phase 7 · M5/M7/M8/M9 Delivery + End-to-End Integration
- **Goal**: complete Personalization, Shadow Validation, the Data Foundation, and Behavioral Analytics, and string them into an end-to-end flow.
- **Work**: deliver M5 (peer fetch + control group), M7 (traffic splitting + dedup to prevent double-sending + **CI non-inferiority test**, Code Review corrected the non-inferiority statistics convention), M8 (onboarding/ID-mapping/wide table/DQC/suppression, fixed the dedup mis-merge bug), M9 (reports + automated insights + in-house RFM/churn/engagement); produce an end-to-end demo + integration tests.
- **Key Decisions**: M7 replaces simple significance with a confidence-interval non-inferiority test; M8 dedup treats event_id as authoritative to avoid mis-merging real events.
- **Deliverables**: M5/M7/M8/M9 modules + e2e demo + integration tests.

### Phase 8 · M6 + Service Decomposition + API Gateway + Architecture Overview
- **Goal**: add AI Copywriting; decompose the platform into services by functional independence.
- **Work**: deliver M6 (multilingual copy + compliance pre-screening, Code Review fixed the "disclaimer truncated" compliance bug); decompose the 9 modules **into 7 independent services by functional independence** (not a monolith) + an **API gateway that only does routing/authentication/rate-limiting**; produce the architecture overview.
- **Key Decisions**: Personalization/Messaging/Analytics, etc., become independent services according to their latency and scaling profiles; the gateway contains no business logic and uses a reverse proxy in production.
- **Deliverables**: `copywriting` module + `src/services/` (7 services) + `src/api_gateway.py` + `ARCHITECTURE.md`.

### Phase 9 · Archiving and Handover
- **Goal**: capture requirements and assessment to facilitate handover.
- **Work**: record all requirement prompts; **audit code vs feature list/technical solution file by file** to produce an implementation comparison report (with completeness %); compile the handover checklist and this work report.
- **Deliverables**: `Growth-requirement-prompt.md`, `Growth-实现对比报告.md`, `Growth-交接清单.md`, `Growth-工作报告.md`.

---

## 3. Results Summary (Quantified)

| Dimension | Result |
|---|---|
| Business modules | **M1–M9 all delivered** (runnable MVP) |
| Service decomposition | 7 independent services + 1 API gateway + shared contract |
| Tests | **269 passing** (17 test files, including e2e integration), CI py3.10–3.12 |
| Code repository | `faye-rao/Growth`, semantic commits per module |
| Differentiation highlights | cross-product funnel, three-solution cohort engine (incl. 2.5-million-scale Bitmap), NL2SQL, cross-campaign frequency capping, Shadow non-inferiority gate, multilingual AI copy, in-house RFM/churn/engagement |
| Documentation | 9 feature lists (CN) + 9 (EN) + overview + 3 technical solutions (CN/EN) + comprehensive analysis + architecture + comparison + handover + prompt records |
| Average feature completeness | **~62%** (core flow + differentiation delivered; see the comparison report for details) |

**Engineering method highlights**: TDD throughout (tests first), independent Code Review per module (which actually found and fixed real bugs such as M3 accounting, M7 non-inferiority statistics, M8 dedup, and M6 compliance truncation), contract-driven parallel development, semantic commits.

---

## 4. TODO to Make the System Truly Run

> Status: it already runs locally (`pytest` 269 passing, `examples/e2e_demo.py` runs through, `uvicorn api_gateway:app` starts the gateway). But this is an **in-memory algorithm/contract MVP**, with a clear gap from a "production system that connects to real data and withstands real traffic". The following is the TODO to reach **production-runnable**, ordered by priority and suggested sequence.

### Step 0 · Immediate (handover day)
- [ ] Log in and verify GitHub Actions CI passes green across the three Python versions (our `gh` is not logged in and cannot read it)
- [ ] Locally `pip install -e ".[dev]" && pytest` to reproduce 269 passing; walk through the gateway routes

### Step 1 · Close Prerequisite Dependencies (decides everything, requires external coordination)
- [ ] **Data Team decides OLAP selection** (ClickHouse/Doris/StarRocks) —— a shared prerequisite for M2/M4/M8
- [ ] Obtain the **event schema + desensitized samples + ID-Mapping table** (Pei Qing / Data Team)
- [ ] Confirm with Growth the **Top Cohorts, the list of reports people actually look at, the frequency policy, and the Shadow scenarios and acceptance criteria**
- [ ] Confirm with the MoEngage vendor the **messaging-stream integration method** (needed for the M7 control)

### Step 2 · P0 Production Infrastructure (the biggest MVP→launch-ready gap)
- [ ] **Real data integration and persistence**: footprint event integration (batch/Kafka) → land in OLAP wide table; persist messaging/conversion logs (currently in-memory contract)
- [ ] **M2 compiled SQL connects to real OLAP** + large-cohort batch-run scheduling (2.5-million scale)
- [ ] **M5 Personalization hot path**: precomputed cohorts + Redis point lookups + cache degradation (currently real-time hits at request time, with QPS/latency not meeting the bar)
- [ ] **M1 sending pipeline**: a Kafka peak-shaving queue to withstand the million scale + integration with Botim Open Platform's real rate-limit interface
- [ ] **Unified time zone Asia/Dubai**: M3/M5 scheduling/quiet hours/attribution to eliminate naive datetime
- [ ] **Authentication/multi-tenancy/audit**: add module-level authentication and a token system (the gateway already has MOE-APPKEY)

### Step 3 · Containerization and Observability (deployment run)
- [ ] Per-service Dockerfile + compose / K8s orchestration (7 services deployed independently)
- [ ] Structured logging + metrics + tracing + alerting
- [ ] OpenAPI contract + contract testing; load testing (M5 fetch hot path, M2 cohort batch run)
- [ ] Security review (PII, rate limiting, UAE Fintech compliance)

### Step 4 · Feature Completion (post-launch iteration)
- [ ] M3: campaign state machine, Flow nodes, campaign templates, quiet hours, A/B/N winner write-back, orchestration UI; M3↔M6 copy integration
- [ ] M7: MoEngage stream integration, reuse the M4 attribution convention, observation period + sequential test early stopping
- [ ] M4: SQL-ize the cross-product funnel, reconciliation discrepancy alerting, ROI
- [ ] M8: Kafka subscription feeding the suppression layer, DQC drift detection
- [ ] M9: align the report list with Growth and reconcile, report export, dimensional anomaly attribution

### Step 5 · AI Increment Main Line (the core increment positioned by the survey, currently mostly stubs)
- [ ] Real LLM integration: M6 copy (protocol already reserved), M2 NL2SQL (templates → RAG+LLM, keeping the fallback)
- [ ] M3 AI orchestration (natural language → cohort + copy + scheduling + Flow, named by the survey as the biggest highlight)
- [ ] M2 intelligent segmentation: Lookalike, propensity scoring, AI suggestions, algorithmic performance optimization
- [ ] M1 delivery optimization: reachability prediction ranking, STO, Next-Best-Channel
- [ ] M9 narrative BI + NL querying

### Launch Cadence Suggestion
**First close prerequisite interviews/data → wire up the real minimal closed loop of "cleansing → single segment → single campaign → send → Shadow control → funnel recovery" for one high-frequency scenario (e.g., Wallet activation Push) → 5% traffic Shadow validation that is no worse than MoEngage → then roll out horizontally + layer on AI increments.**

---

## 5. Risks and Dependencies
- **Dependencies not closed**: OLAP selection, data samples, the report/Cohort list, the MoEngage stream, etc., are still largely "to be confirmed" —— the root cause of the ±30% estimate; they must be closed before starting.
- **Do not over-trust the MVP**: there is currently no persistence/real data source/real LLM, so it cannot face real traffic directly.
- **Trustworthy numbers are a prerequisite for replacement**: M4/M9 reports must be dual-run and reconciled against the old system before operations will trust them.
- **Conventions not unified**: there is no company-wide definition of conversion/active/retention; attribution must be aligned before development.
- **Shadow double-send**: before going live with real Shadow, the M7 dedup middle layer must be integrated with both real sending channels.
