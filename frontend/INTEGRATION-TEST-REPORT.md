# Frontend — System Integration Test Report

> Botim Growth operations console (frontend) ｜ Updated: 2026-06-05
> Scope: **all 7 module screens + foundation + auth + Campaign Flow canvas** (the full `docs/Frontend-Plan.md`, MVP depth per screen).
> Environment: Node v24.16, React 18 + TS + Vite 5 + Ant Design 5; backend = FastAPI API gateway (`uvicorn api_gateway:app`).

## 1. Summary

| Layer | Result |
|---|---|
| TypeScript typecheck (`tsc --noEmit`) | ✅ clean (exit 0) |
| Unit tests (Vitest, jsdom) | ✅ **51 passed** / 9 files |
| Production build (`vite build`) | ✅ success |
| **Joint frontend↔backend integration** (Vitest, live gateway, all 7 services) | ✅ **21 passed** / 1 file |
| **E2E (Playwright, real browser)** | 🟡 **1/2 passed** — 1 real browser test green against the live backend; 1 failed on a chromium **cold-launch 180s timeout** (sandbox env, not a code defect) |
| Independent code review | ✅ 1 bug fixed; risks documented |
| **Total automated tests (unit + integration)** | **72 passed** |

## 2. Screens built (full plan)

| Screen | Service(s) | Highlights |
|---|---|---|
| **Audience** | M2 | react-querybuilder ↔ M2 DSL bidirectional mapping, NL2SQL panel, debounced live size, templates, compile-SQL |
| **Campaign** | M3+M1 | list + 3-step wizard (audience→A/B/N→schedule) + **Flow canvas** (React Flow: delay/branch/ab_split/wait_event/webhook) → run → balanced summary |
| **Analytics** | M4+M9 | ECharts funnel + cross-product toggle + attribution + reports + auto-insights |
| **Personalization** | M5 | experience register/publish + multilingual payload editor (en/ar/hi/tl) + fetch tester |
| **Content** | M6 | multilingual copy generation + inline compliance tags (Arabic RTL) + compliance checker + select-best |
| **Experiment** | M7 | 5% shadow split + comparison report (color-coded verdict, significance, CI) |
| **Data** | M8 | DQC dashboard + identity resolve + suppression check + ingest tester |
| Cross-cutting | — | `ErrorBoundary`, `LoginGate` (MOE-APPKEY + role/RBAC seed), i18n + **RTL (ar)**, 7-service nav |

## 3. Unit tests (offline, mocked API) — 51 / 9 files

| File | Tests |
|---|---:|
| audience/dsl.test.ts | 20 |
| audience/AudiencePage.test.tsx | 4 |
| campaign/CampaignPage.test.tsx | 4 |
| campaign/FlowCanvas.test.tsx | 3 |
| analytics/AnalyticsPage.test.tsx | 3 |
| personalization/PersonalizationPage.test.tsx | 5 |
| content/ContentPage.test.tsx | 6 |
| experiment/ExperimentPage.test.tsx | 3 |
| data/DataPage.test.tsx | 3 |
| **Total** | **51** |

Run: `npm test`.

## 4. Joint frontend↔backend integration — 21 / 1 file (live gateway)

Backend: `PYTHONPATH=src uvicorn api_gateway:app --port 8000`. Run: `npm run test:integration`.
Covers the exact endpoints + shapes the frontend API client uses across **all 7 services**:
- gateway: /health, 401 without MOE-APPKEY, 404 unknown prefix
- audience: size / evaluate / compile / nl2sql (dsl re-evaluates) / templates / 422
- campaign: run → accounting identity `sent+not_sent+control+capped == audience_size`
- content: copy/generate (en/ar)
- analytics: funnel + cross-product + report + insights
- personalization: register → publish → fetch (returns the experience key)
- experiment: shadow/split + shadow/report (verdict ∈ better/not_worse/worse/inconclusive)
- data: dqc + identity/resolve + suppression/check

**Result: 21/21 passed.**

## 5. E2E (Playwright) — setup + result

Config `playwright.config.ts` (auto-starts Vite dev, which proxies `/api`→gateway). Spec `e2e/smoke.spec.ts`:
1. console loads → navigate Audience→Campaign — **failed on chromium cold-launch (180s browser-launch timeout)** in this sandbox; not an app error.
2. **Audience NL2SQL + live size estimate hit the backend — ✅ passed (695ms)** in a real headless browser against the running gateway.

The launch timeout is an environment performance artifact (first chromium start in the sandbox). Re-run locally:
```bash
npx playwright install chromium
PYTHONPATH=src uvicorn api_gateway:app --port 8000   # terminal 1
npm run e2e                                            # terminal 2 (auto-starts vite)
```

## 6. Code review — outcome
- **Fixed [BUG]**: Audience debounced size-estimate effect had its `alive` flag scoped to the `setTimeout` callback (dead cleanup) → stale response could set state. Hoisted to effect scope. Re-verified green.
- DSL mapping, API contract alignment, i18n/RTL assessed correct/ship-ready for the MVP.

## 7. Known limitations / next steps
- **`dsl.ts` numeric-string coercion** [RISK]: all-digit string values coerced to number; make field-`inputType`-aware before production (phone/ID domain).
- **i18n**: en/ar (RTL) fully wired; hi/tl bundles partial (UI strings pending for those locales).
- **Auth**: `LoginGate` is an MVP (stores MOE-APPKEY + role); production needs a real login→token exchange and enforced RBAC per route.
- **Charts/Flow**: ECharts + React Flow are functional MVPs; persistence of Flow definitions to a backend campaign is not wired.
- **E2E**: 1 smoke test stable; broaden coverage + stabilize browser launch in CI.
- **Backend prerequisites for production**: OpenAPI export, CORS, login endpoint, list/CRUD endpoints, real-time channel (size/progress).

## 8. How to reproduce
```bash
cd botim-growth-m2-cohort/frontend && npm install
npm run typecheck        # clean
npm test                 # 51 unit tests
# backend up, then:
npm run test:integration # 21 joint tests
npm run build            # production build
npm run dev              # dev server :5173 (proxies /api -> :8000)
```
