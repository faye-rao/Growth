import { defineConfig } from "vitest/config";

// Joint frontend<->backend integration tests: hit the REAL running API gateway
// (uvicorn api_gateway:app on :8000). Node environment, no jsdom.
// Start the backend first:  PYTHONPATH=src uvicorn api_gateway:app --port 8000
export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["integration/**/*.test.ts"],
    testTimeout: 20000,
    hookTimeout: 20000,
  },
});
