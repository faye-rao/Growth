# Growth Platform · Handover Checklist (Handover)

> Handover date: **2026-06-05 (refreshed)** ｜ Repository: `https://github.com/faye-rao/Growth` (default branch main)
> Local: `C:\Faye\Growth\botim-growth-m2-cohort` (code, including `frontend/`) ＋ `C:\Faye\Growth\*.md` (analysis documents)
> Companion docs: `Growth-实现对比报告.md`/`Growth-Implementation-Audit.md` (per-feature implementation level), `ARCHITECTURE.md` (architecture), `Frontend-Plan.md` (frontend plan), `TEST-REPORT.md`, `PRODUCT-CONTEXT.md`, `Growth特性清单-M*-1.md`/`Growth技术方案-*.md` (requirements/technology selection), `Growth-requirement-prompt.md`
> The `CLAUDE.md` files at each level (repo root / src subdirectories / frontend) are project memory auto-loaded into AI sessions, containing conventions/commands/current state.

---

## A. Project Background (30 seconds)
Build an in-house **user growth platform** for Botim (Dubai, launching in the UAE, target users ≈ 2.5 million), replacing the competing product MoEngage. Scope and priorities come from the interview survey (`用增问题survey-updated v3.xlsx`).
Current state: **backend 9 modules M1–M9** built into a runnable, testable MVP, split into **7 services + 1 API gateway** by functional independence; **frontend Operations Console, 7-screen MVP** built and jointly integrated with the backend end-to-end; CI integrated.

---

## B. Completed Work

### B1. Backend (repo root `src/`)
- **9 business modules** (Python, zero core dependencies): `cohort_engine`(M2), `messaging`(M1), `orchestration`(M3), `analytics`(M4), `personalization`(M5), `copywriting`(M6), `shadow`(M7), `data_foundation`(M8), `behavioral`(M9)
- **Shared contracts** `growth_common` (DeliveryRecord messaging log, MessagingGateway protocol, deterministic bucketing stable_fraction)
- **7 services** (`src/services/`, each an independent FastAPI app) + **API gateway** `src/api_gateway.py` (prefix routing + MOE-APPKEY auth 401 + token-bucket rate limiting 429 + /health)
- **End-to-end**: `examples/e2e_demo.py` + `tests/test_integration_e2e.py`
- **Backend tests: 269 passed** (17 files); coverage ~90%

### B2. Frontend (`frontend/`, newly added this round) ★
- **Tech stack**: React 18 + TS + Vite + Ant Design 5 + React Router + TanStack Query + i18n (**en/ar + RTL**); dev proxy `/api→:8000`.
- **Foundation**: 7-service left-nav layout, `LoginGate` (MOE-APPKEY + role), `ErrorBoundary`, typed API client, M2 DSL types.
- **All 7 screens** (all at MVP depth, with tests):
  - Audience (M2): rule builder ↔ M2 DSL **bidirectional mapping** + NL2SQL + live audience-size estimate + templates + Compile SQL
  - Campaign (M3+M1): list + 3-step wizard (select audience → A/B/N → scheduling) + **React Flow Flow canvas** + frequency capping + RunResult
  - Analytics (M4+M9): ECharts funnel + cross-product + attribution + reports + auto insights
  - Personalization (M5): experience registration/publishing + multilingual payload editor + fetch tester
  - Content (M6): multilingual copy generation + inline compliance (Arabic RTL) + compliance check + best-variant selection
  - Experiment (M7): 5% traffic split + control report (decision/significance/CI)
  - Data (M8): DQC dashboard + identity resolution + suppression check + ingest
- **Frontend tests**: unit tests **51** (9 files) + **joint integration 21** (against the real gateway, all 7 services) = **72 passed**; E2E (Playwright) 1/2 (1 real-browser case passed; 1 timed out on chromium cold start, not a code issue). See `../frontend/INTEGRATION-TEST-REPORT.md` for details.
- **Runnable verification**: already run and screenshotted in a real browser (LoginGate / Audience / Campaign).

### B3. Differentiating Highlights (vs. MoEngage)
Cross-product funnel (M4) · three-strategy cohort segmentation engine (M2, including 2.5-million-scale RoaringBitmap) · NL2SQL cohort segmentation (M2) · cross-campaign frequency capping & dedup (M3) · Shadow non-inferiority gate (M7) · multilingual AI copywriting + compliance (M6) · in-house RFM/churn/engagement (M9).

### B4. CI and Documentation
- **CI**: `.github/workflows/ci.yml` (push/PR, runs pytest + coverage on py3.10/3.11/3.12), **results published to the Actions run Summary + JUnit/coverage artifacts**.
- **Documentation (repo `docs/`)**: requirements checklist (CN/EN), technology proposal (CN/EN), comprehensive analysis, `ARCHITECTURE.md`, **Implementation Audit (CN/EN)**, **test report `TEST-REPORT.md`**, **frontend plan `Frontend-Plan.md` (CN/EN)**, **product-level context `PRODUCT-CONTEXT.md`**, work reports (CN/EN), this handover checklist (CN/EN).
- **CLAUDE.md memory**: repo root + `src/cohort_engine/` + `src/services/` + `frontend/` (including work-item status checklist); `CLAUDE.local.md` for local exceptions (gitignored).

### B5. Completeness Snapshot
- Backend functionality (against the survey feature checklist): average **~62%** (M1~60/M2~65/M3~50/M4~80/M5~60/M6~65/M7~55/M8~65/M9~60); the core path + differentiation are in place, while the AI mainline / production infrastructure remain to be built (see the Implementation Audit for details).
- Frontend: all 4 planned phases completed end-to-end, **7-screen MVP depth** (see the "work-item status checklist" at the end of `frontend/CLAUDE.md`).

---

## C. Remaining Work Checklist

### C0. 🔴 Immediately Actionable
- [ ] **Verify CI is green**: on the repo Actions page, check the three Python versions running tests + the coverage artifacts (our `gh` is not logged in, so we cannot read it on your behalf).
- [ ] **Start services locally and self-test**: backend `pip install -e ".[dev]" && pytest` (269); frontend `cd frontend && npm install && npm test` (51) + after starting `uvicorn api_gateway:app`, run `npm run test:integration` (21) / `npm run dev` to view the UI (log in with `demo-appkey`).

### C1. 🟥 P0 Backend Prerequisites (unblocks the frontend from mock to direct production connection + the biggest gap to launch)
- [ ] **Export OpenAPI + CORS + login token-exchange endpoint + list/save/CRUD endpoints + real-time channel** (5 hard frontend dependencies; currently dev relies on Vite proxy + MOE-APPKEY header).
- [ ] **Persistence and real data integration**: footprint event ingestion (Kafka/batch), wide tables persisted to OLAP (Data Team to decide), messaging/conversion logs persisted to storage (currently in-memory contracts).
- [ ] **M2 compiled SQL against real OLAP** + large-audience batch scheduling.
- [ ] **M5 personalization hot path**: precomputed audiences + Redis point lookups + cache fallback; add scheduling + time zone (Asia/Dubai), active/ended states, conversion goals.
- [ ] **M1 send pipeline**: Kafka peak shaving, integration with Botim's real rate-limit interface, logs persisted to storage.
- [ ] **Unify time zone to Asia/Dubai** (M3/M5 currently use naive datetime); **auth/multi-tenancy/RBAC enforcement/audit**.

### C2. 🟧 P1 Feature Completion (by module)
- [ ] **M3↔M6 wiring**: inject M6 copy into M3 A/B/N variants; feed A/B/N significance winners back (the test resides in M7); persist Flow definitions to the campaign.
- [ ] **M1 In-App**: campaign slot/page configuration, page-level frequency capping, SDK self-rendering delivery.
- [ ] **M7 Shadow**: MoEngage messaging-stream integration (requires the vendor), reuse M4 attribution definitions, configurable observation window + sequential testing, CUPED.
- [ ] **M4**: SQL-ify the cross-product funnel, reconciliation-discrepancy alerts, ROI.
- [ ] **M8**: Kafka subscription feeding the suppression layer, DQC drift detection, Mapping accuracy, tag dictionary.
- [ ] **M9**: align with Growth on the "reports people actually look at" list and reproduce them (prove the numbers reconcile), report export, dimensional anomaly attribution.

### C3. 🟨 P2 AI Incremental Mainline (the survey positions "incremental value comes from AI"; currently mostly stubs)
- [ ] Real LLM integration: M6 copy (`CopyProvider` protocol already reserved), M2 NL2SQL (template → RAG+LLM, keep the fallback).
- [ ] M3 AI orchestration (natural language → audience + copy + scheduling + Flow); M2 intelligent segmentation (Lookalike/propensity/AI suggestions/algorithmic optimization); M1 delivery optimization (reachability prediction/STO/Next-Best-Channel); M6 outcome learning; M9 narrative BI + NL data Q&A.

### C4. 🟩 Frontend Wrap-up + Engineering for Launch
- [ ] **Frontend**: improve `dsl.ts` numeric-string coercion per field type, complete hi/tl copy, enforce RBAC by route/by button, a11y, expand E2E coverage + stabilize in CI, ESLint/Prettier, Storybook, switch API types to openapi-typescript auto-generation.
- [ ] **Bring the frontend into CI**: add a frontend job running tsc + vitest + build.
- [ ] **Containerization/deployment**: Dockerfile/compose for each service + frontend, K8s, gateway reverse proxy; observability (logs/metrics/tracing/alerting); security review (PII, rate limiting, UAE Fintech compliance).

---

## D. Key Dependencies & Blockers (require external coordination)
| Owner | To provide | Blocked work |
|---|---|---|
| **Data Team (Mr. Ma)** | OLAP selection, ER diagram/tables, ID-Mapping + coverage, T+1 cleansing, masked samples, historical-query SQL distribution | All of C1, M2/M8, NL2SQL |
| **Growth (Dubai, Radhika)** | Top Cohort definitions, the list of reports actually used, Flow node types, frequency policy, Shadow scenarios and acceptance criteria | Finalizing M2/M3/M4/M7/M9 |
| **Pei Qing** | Event schema, data samples, arranging on-site shadowing in Dubai | M8 integration, kicking off overall work |
| **MoEngage vendor** | Messaging-stream integration method/latency, hidden Webhook/Connector | M7 Shadow control |

> ⚠️ Most are still "to be asked / to be confirmed" — **prioritize closing these interviews before starting work**. Estimates carry a ±30% range until the data/answers are in place.

---

## E. Onboarding (new colleagues)
**Backend**
1. `git clone https://github.com/faye-rao/Growth && cd Growth`
2. `python -m pip install -e ".[dev]"` → `pytest` (should be 269 passed)
3. Read `docs/PRODUCT-CONTEXT.md` (background) → `ARCHITECTURE.md` (7 services + gateway) → `README.md`
4. `PYTHONPATH=src uvicorn api_gateway:app --port 8000` → check `/health`, `python examples/e2e_demo.py`

**Frontend**
5. `cd frontend && npm install` → `npm test` (51) → `npm run dev` (:5173, log in with `demo-appkey`); with the backend running, `npm run test:integration` (21)
6. Read `frontend/CLAUDE.md` (conventions + status checklist), `frontend/INTEGRATION-TEST-REPORT.md`

**Claiming tasks**: cross-reference `docs/Growth-实现对比报告.md` (each module's "done/gaps") + section C of this checklist.

## F. Risks
- **MVP ≠ production**: the backend is in-memory / has no real data source / no real LLM, and the frontend's 7 screens are at MVP depth — do not point real traffic at it directly.
- **Number credibility**: replacing MoEngage is predicated on "the numbers reconcile"; M4/M9 reports must be dual-run and reconciled against the old system.
- **Definitions not unified**: conversion/active/retention have no company-wide definitions; attribution must first align on definitions.
- **Shadow dual-send**: before going live with real Shadow, the M7 dedup middle layer must be wired to two real channels.
- **Frontend productionization blocker**: until the C1 backend prerequisites (OpenAPI/CORS/login/CRUD/real-time channel) are filled, the frontend can only use the dev proxy + MOE-APPKEY header.
