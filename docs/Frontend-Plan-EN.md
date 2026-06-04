# Frontend Work Plan — Botim Growth Operations Console

> Goal: Build an **Operations Console** on top of the existing 7 backend services + API gateway, replicating MoEngage's audience rule editor, 3-step campaign wizard, Flow canvas, and reports.
> For the Chinese version, see `Frontend-Plan.md`. For the current implementation status, see the bottom of `../frontend/CLAUDE.md` and `../frontend/INTEGRATION-TEST-REPORT.md`.

## 1. Tech Stack
| Dimension | Choice | Rationale |
|---|---|---|
| Framework | React 18 + TypeScript + Vite | Consistent with competitor's shape; mature ecosystem |
| UI library | Ant Design 5 | Data-dense back office + built-in RTL |
| rule builder | react-querybuilder | Nested rules ↔ M2 JSON DSL bidirectional mapping |
| orchestration/Flow canvas | React Flow | M3 Flow nodes (delay / branch / A·B / wait-for-event / webhook) |
| Charts | ECharts | M4 funnel / cross-product funnel |
| Server state / local state | TanStack Query + Zustand | REST fetch caching + local state |
| Form validation | React Hook Form + Zod | payload / rule validation |
| Internationalization | react-i18next + RTL | en/ar/hi/tl, Arabic RTL |
| API client | openapi-typescript (generated from gateway /openapi.json) | Type safety, contract alignment |
| Testing | Vitest + Testing Library + Playwright | Component + E2E |

## 2. Backend Prerequisites (frontend dependencies)
1. Each service exports `/openapi.json` via FastAPI; the gateway aggregates them.
2. CORS (browser cross-origin); during development, work around it with the Vite dev proxy.
3. A login-to-token endpoint (currently only MOE-APPKEY header validation).
4. List / save / CRUD endpoints (cohort save, campaign list, experience CRUD).
5. Real-time channel (audience-size estimate, send progress; polling or WebSocket).

## 3. Screen ↔ Service Mapping
| Screen | Service | Key components |
|---|---|---|
| Campaign (highest priority) | campaign(M3+M1) | Campaign list + 3-step wizard (audience → content A/B/N → schedule & goal) + Flow canvas + frequency capping settings + send status |
| Audience | audience(M2) | Visual rule builder + NL2SQL input + real-time audience-size estimate + template library + cohort list/save |
| Analytics | analytics(M4+M9) | Funnel chart + cross-product funnel + attribution + reports + auto-insights stream |
| Personalization | personalization(M5) | experience list + 3-step wizard + payload editor + publish toggle + fetch tester |
| Content | content(M6) | Multilingual copy generation + inline compliance hints + preview/edit + bind to campaign variants |
| Experiment | experiment(M7) | Shadow config (5% traffic split) + comparison report (significance / non-inferiority conclusion) |
| Data | data-platform(M8) | Identity lookup + DQC dashboard + suppression list (more internal ops-oriented) |

## 4. Implementation Steps (4 phases)
- **Phase 0 · Scaffolding (~5 person-days)**: Vite+TS+AntD, ESLint/Prettier, environment configuration, generate client from OpenAPI, Vite dev proxy.
- **Phase 1 · Foundation (~12 person-days)**: design system/theming, layout (left nav mapping to the 7 services), login/authentication, i18n+RTL, unified loading/error/empty states, routing.
- **Phase 2 · Module screens (~79 person-days)**: by priority — Campaign(18) + Audience(15) + Analytics(14) + Personalization(12) + Content(8) + Experiment(6) + Data(6).
- **Phase 3 · Cross-cutting (~8 person-days)**: full RTL, accessibility, RBAC, auditing.
- **Phase 4 · Testing & delivery (~10 person-days)**: component tests (Vitest), E2E (Playwright), Storybook, CI, build/deploy (Docker + gateway reverse proxy).

## 5. Effort & Timeline
- Frontend ≈ **114 person-days** + backend prerequisites ≈ 15 person-days = **~130 person-days**.
- A 2–3 person frontend team: full scope ~2.5–3 months; MVP subset (Campaign+Audience+Content+basic Analytics) ~6–7 weeks.

## 6. Sequencing
Backend first exports OpenAPI + login + CORS → Phase 0/1 foundation (including RTL) → **Campaign 3-step wizard + Audience rule builder first** → Content → Analytics → then Personalization/Experiment/Data → E2E + deployment.

## 7. Key Risks
- **Arabic RTL** must be included from day 1 (core market; retrofitting later is costly).
- Backend contract gaps (list/save/CRUD, login, real-time channel) must be filled first, otherwise the frontend is blocked.
- Analytics numbers must be reconciled with the backend/legacy system before operations will trust them.
- The **rule builder ↔ M2 DSL bidirectional mapping** is the core difficulty of the Audience screen (output convertible to DSL, DSL renderable back).
