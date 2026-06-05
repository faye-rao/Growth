import { test, expect } from "@playwright/test";

// Seed the MOE-APPKEY so the LoginGate is satisfied (the API client reads it too).
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("MOE_APPKEY", "demo-appkey");
    localStorage.setItem("MOE_ROLE", "operator");
  });
});

test("console loads and navigates Audience -> Campaign", async ({ page }) => {
  await page.goto("/");
  // default route -> Audience
  await expect(page.getByText(/Audience/i).first()).toBeVisible();

  // navigate to Campaign via the side nav
  await page.getByRole("link", { name: /Campaign/i }).click();
  await expect(page).toHaveURL(/\/campaign/);
  await expect(page.getByText(/Campaign/i).first()).toBeVisible();
});

test("Audience NL2SQL + live size estimate hit the backend", async ({ page }) => {
  await page.goto("/audience");
  // type a natural-language audience and translate (NL2SQL via the gateway)
  const nl = page.getByLabel("nl2sql-input");
  await nl.fill("KYC users with balance over 100");
  await page.getByRole("button", { name: /Translate/i }).click();
  // confidence appears once the backend responds
  await expect(page.getByTestId("nl-confidence")).toBeVisible({ timeout: 10000 });
});
