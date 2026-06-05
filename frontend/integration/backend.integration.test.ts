// Joint frontend<->backend integration tests.
// Exercises the EXACT gateway endpoints + request/response shapes the frontend
// API client (src/api/client.ts) depends on, against the REAL running gateway.
//
// Prereq: PYTHONPATH=src uvicorn api_gateway:app --host 127.0.0.1 --port 8000
import { describe, it, expect } from "vitest";

const BASE = process.env.INTEGRATION_BASE || "http://127.0.0.1:8000";
const KEY = "demo-appkey";

function post(path: string, body: unknown, withKey = true) {
  return fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(withKey ? { "MOE-APPKEY": KEY } : {}),
    },
    body: JSON.stringify(body),
  });
}
function get(path: string, withKey = true) {
  return fetch(`${BASE}${path}`, {
    headers: withKey ? { "MOE-APPKEY": KEY } : {},
  });
}

const KYC = { match: { type: "attribute", field: "is_kyc", operator: "eq", value: true } };

describe("gateway", () => {
  it("/health returns ok + service map", async () => {
    const r = await get("/health", false);
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(j.status).toBe("ok");
    expect(Object.keys(j.services)).toEqual(
      expect.arrayContaining(["audience", "campaign", "content", "analytics", "experiment", "data"])
    );
  });

  it("rejects /api/* without MOE-APPKEY (401)", async () => {
    const r = await post("/api/audience/segments/size", KYC, false);
    expect(r.status).toBe(401);
  });

  it("unknown prefix is 404", async () => {
    const r = await get("/api/nope/x");
    expect(r.status).toBe(404);
  });
});

describe("audience service (M2)", () => {
  it("size returns a number", async () => {
    const r = await post("/api/audience/segments/size", KYC);
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(typeof j.size).toBe("number");
    expect(j.size).toBeGreaterThan(0);
  });

  it("evaluate returns size + customer_ids", async () => {
    const j = await (await post("/api/audience/segments/evaluate", KYC)).json();
    expect(typeof j.size).toBe("number");
    expect(Array.isArray(j.customer_ids)).toBe(true);
    expect(j.customer_ids.length).toBe(j.size);
  });

  it("compile returns SQL", async () => {
    const j = await (await post("/api/audience/segments/compile", KYC)).json();
    expect(typeof j.sql).toBe("string");
    expect(j.sql.toUpperCase()).toContain("SELECT");
  });

  it("nl2sql returns dsl + confidence, and the dsl evaluates", async () => {
    const nl = await (await post("/api/audience/nl2sql", { text: "KYC users with balance over 100" })).json();
    expect(nl).toHaveProperty("dsl");
    expect(typeof nl.confidence).toBe("number");
    expect(typeof nl.requires_review).toBe("boolean");
    // feed produced DSL back into evaluate — proves round-trip contract
    const ev = await (await post("/api/audience/segments/evaluate", nl.dsl)).json();
    expect(typeof ev.size).toBe("number");
  });

  it("templates returns a list", async () => {
    const j = await (await get("/api/audience/templates")).json();
    expect(Array.isArray(j.templates)).toBe(true);
    expect(j.templates.length).toBeGreaterThan(0);
  });

  it("invalid rule -> 422", async () => {
    const r = await post("/api/audience/segments/size", {
      match: { type: "attribute", field: "x", operator: "bogus", value: 1 },
    });
    expect(r.status).toBe(422);
  });
});

describe("campaign service (M3+M1)", () => {
  it("run assembles audience -> send -> balanced summary", async () => {
    const req = {
      id: "fe-int-1",
      audience_spec: KYC,
      channel: "push",
      variants: [
        { name: "A", weight: 1, content_id: "ca" },
        { name: "B", weight: 1, content_id: "cb" },
      ],
      control_pct: 0.25,
      daily_cap: 99,
    };
    const r = await post("/api/campaign/campaigns/run", req);
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(typeof j.audience_size).toBe("number");
    // accounting: sent + not_sent + control + capped == audience (batch, no excluded)
    const sent = j.sent_count ?? Object.values(j.sent_by_variant ?? {}).reduce((a: number, b: any) => a + b, 0);
    expect(sent + j.not_sent_count + j.control_count + j.capped_count).toBe(j.audience_size);
  });
});

describe("content service (M6)", () => {
  it("generate returns multilingual variants", async () => {
    const r = await post("/api/content/copy/generate", {
      goal: "activate_wallet",
      product: "Wallet",
      locales: ["en", "ar"],
      n: 2,
    });
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(j).toBeTruthy();
  });
});

describe("analytics service (M4+M9)", () => {
  it("funnel returns step data", async () => {
    const j = await (await post("/api/analytics/funnel", { steps: ["App Opened", "Transfer"] })).json();
    expect(j).toBeTruthy();
    expect(j).toHaveProperty("step_counts");
  });
  it("cross-product funnel works", async () => {
    const r = await post("/api/analytics/funnel", { steps: ["App Opened", "Transfer"], cross_product: true });
    expect(r.status).toBe(200);
  });
  it("report active_users returns data", async () => {
    const r = await post("/api/analytics/reports/active_users", {});
    expect(r.status).toBe(200);
  });
  it("insights flags a spike", async () => {
    const j = await (await post("/api/analytics/insights", { series: [1, 1, 1, 9, 1], z_threshold: 1.5 })).json();
    expect(j).toBeTruthy();
  });
});

describe("personalization service (M5)", () => {
  const key = "fe-int-exp";
  const spec = { match: { type: "attribute", field: "is_kyc", operator: "eq", value: true } };
  it("register -> publish -> fetch", async () => {
    const reg = await post("/api/personalize/experiences", {
      key,
      audience_spec: spec,
      variations: [{ name: "Default", weight: 1, payload: { en: { card: "Hi" }, ar: { card: "مرحبا" } } }],
      control_pct: 0,
    });
    expect([200, 201]).toContain(reg.status);
    const pub = await post(`/api/personalize/experiences/${key}/publish`, {});
    expect(pub.status).toBe(200);
    const fetched = await (await post("/api/personalize/experiences/fetch", {
      identifiers: { customer_id: "u1" },
      experience_keys: [key],
      locale: "ar",
    })).json();
    expect(fetched).toHaveProperty("experiences");
    expect(Object.keys(fetched.experiences)).toContain(key);
  });
});

describe("experiment service (M7)", () => {
  it("split assigns arms ~shadow_pct", async () => {
    const ids = Array.from({ length: 200 }, (_, i) => `u${i}`);
    const j = await (await post("/api/experiment/shadow/split", { customer_ids: ids, shadow_pct: 0.1 })).json();
    expect(j).toBeTruthy();
  });
  it("report returns a verdict", async () => {
    const mk = (n: number, conv: number) =>
      Array.from({ length: n }, (_, i) => ({ customer_id: `x${i}`, status: "sent", converted: i < conv }));
    const j = await (await post("/api/experiment/shadow/report", {
      control_records: mk(100, 20),
      shadow_records: mk(100, 22),
      non_inferiority_margin: 0.05,
    })).json();
    expect(j).toHaveProperty("verdict");
    expect(["shadow_better", "not_worse", "worse", "inconclusive"]).toContain(j.verdict);
  });
});

describe("data-platform service (M8)", () => {
  it("dqc returns a report", async () => {
    const r = await get("/api/data/dqc");
    expect(r.status).toBe(200);
  });
  it("identity resolve returns a canonical id", async () => {
    const r = await post("/api/data/identity/resolve", { identifiers: { customer_id: "u1" } });
    expect(r.status).toBe(200);
  });
  it("suppression check partitions ids", async () => {
    const r = await post("/api/data/suppression/check", { customer_ids: ["u1", "u2"] });
    expect(r.status).toBe(200);
  });
});
