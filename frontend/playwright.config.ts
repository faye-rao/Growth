import { defineConfig } from "@playwright/test";

// E2E: drives the real built app (Vite dev server) which proxies /api -> the
// backend gateway (uvicorn api_gateway:app on :8000 — start it before running).
//   npx playwright install chromium
//   npm run e2e
export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 120000,
  },
});
