# Frontend — System Integration Test Report

> Botim Growth operations console (frontend) ｜ Generated: 2026-06-05
> Scope of this build: **foundation + Audience + Campaign** screens (MVP slice of `docs/Frontend-Plan.md`).
> Environment: Node v24.16, React 18 + TS + Vite 5 + Ant Design 5; backend = FastAPI API gateway (`uvicorn api_gateway:app`).

## 1. Summary

| Layer | Result |
|---|---|
| TypeScript typecheck (`tsc --noEmit`) | ✅ clean (exit 0) |
| Unit tests (Vitest, jsdom) | ✅ **28 passed** / 3 files |
| Production build (`vite build`) | ✅ success (3078 modules) |
| **Joint frontend↔backend integration** (Vitest, live gateway) | ✅ **11 passed** / 1 file |
| Independent code review | ✅ 1 real bug fixed; risks documented |
| **Total automated tests** | **39 passed, 0 failed** |

## 2. Unit tests (offline, mocked API)

| File | Tests | Covers |
|---|---:|---|
| `src/features/audience/dsl.test.ts` | 20 | react-querybuilder ↔ M2 DSL **bidirectional mapping** (operators, and/or/not, valueless/list/between, nested round-trip, event-node lossless round-trip) |
| `src/features/audience/AudiencePage.test.tsx` | 4 | NL2SQL translate→loads DSL + confidence/review tag; debounced size estimate calls API & renders count; templates load |
| `src/features/campaign/CampaignPage.test.tsx` | 4 | 3-step wizard navigation; variant add/remove; Run assembles correct `CampaignRunRequest` & renders summary; zero-variant validation blocks Run |

Run: `npm test` (alias `vitest run`).

## 3. Joint frontend↔backend integration (against the REAL gateway)

Backend started with `PYTHONPATH=src uvicorn api_gateway:app --host 127.0.0.1 --port 8000`.
Tests issue the exact endpoints + request/response shapes the frontend API client
(`src/api/client.ts`) depends on. Run: `npm run test:integration`.

| # | Test | Validates |
|---|---|---|
| 1 | `GET /health` → 200 + service map | gateway up, 7 services mounted |
| 2 | `/api/*` without `MOE-APPKEY` → 401 | gateway auth |
| 3 | unknown prefix → 404 | gateway routing |
| 4 | audience `segments/size` → `{size:number}` | M2 size estimate (UI live count) |
| 5 | audience `segments/evaluate` → `{size, customer_ids[]}` (len matches) | M2 evaluate |
| 6 | audience `segments/compile` → `{sql}` containing SELECT | compile-to-SQL |
| 7 | audience `nl2sql` → `{dsl, confidence, requires_review}`, dsl re-evaluates | NL2SQL round-trip the UI relies on |
| 8 | audience `templates` → non-empty list | template library |
| 9 | invalid rule → 422 | error contract (UI surfaces 4xx) |
| 10 | campaign `campaigns/run` → balanced summary (`sent+not_sent+control+capped == audience_size`) | M3+M1 orchestration+send accounting |
| 11 | content `copy/generate` (en/ar) → variants | M6 multilingual copy |

**Result: 11/11 passed** (114 ms). Confirms the frontend's contract with all the
services it calls is correct end-to-end.

## 4. Code review (independent) — outcome

- **Fixed [BUG]**: Audience debounced size-estimate effect had its `alive` flag scoped to the
  `setTimeout` callback (dead cleanup) → a stale in-flight response could set state after the
  query changed. Hoisted `alive` to effect scope with real cleanup. Re-verified: tsc clean, 28 unit tests pass.
- Reviewer's "missing `src/test/setup.ts`" was a **false positive** — the file exists and the suite runs green.
- DSL mapping, API contract alignment, i18n/RTL (`dir` on `<html>` + ConfigProvider), and test quality assessed **correct / ship-ready** for the MVP.

## 5. Known limitations / next steps (tracked)
- **`dsl.ts` numeric-string coercion** [RISK]: an all-digit string value (e.g. `country = "971"`) is coerced to a number. Given the phone/ID-keyed domain, make coercion field-`inputType`-aware before production.
- **i18n**: `en`/`ar` (with RTL) implemented; `hi`/`tl` resource bundles pending.
- **Screens**: only Audience + Campaign are built; Analytics / Personalization / Content / Experiment / Data are placeholder routes (see `docs/Frontend-Plan.md` for the remaining ~79 person-days).
- **Backend prerequisites for production**: OpenAPI export, CORS, login→token endpoint, list/CRUD endpoints, real-time channel (size/progress) — currently dev uses Vite proxy + MOE-APPKEY header.
- E2E browser tests (Playwright) not yet added (unit + node-level joint integration only).

## 6. How to reproduce
```bash
# backend (terminal 1)
cd botim-growth-m2-cohort
PYTHONPATH=src python -m uvicorn api_gateway:app --host 127.0.0.1 --port 8000

# frontend (terminal 2)
cd botim-growth-m2-cohort/frontend
npm install
npm run typecheck         # clean
npm test                  # 28 unit tests
npm run test:integration  # 11 joint tests (needs backend running)
npm run build             # production build
npm run dev               # dev server at :5173 (proxies /api -> :8000)
```
