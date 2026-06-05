// Thin API client to the backend API gateway (proxied at /api in dev).
// Every /api/* call carries the MOE-APPKEY header (gateway auth).
import type {
  SegmentSpec,
  EvaluateResult,
  NL2SQLResult,
} from "./types";

const BASE = "/api";

function appKey(): string {
  return (
    (typeof localStorage !== "undefined" && localStorage.getItem("MOE_APPKEY")) ||
    "demo-appkey"
  );
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "MOE-APPKEY": appKey(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = (j && (j.detail || j.message)) || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, `${res.status}: ${detail}`);
  }
  // some endpoints may return empty
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
};

// ---- typed helpers per service ------------------------------------------------

// Audience (M2)
export const audienceApi = {
  evaluate: (spec: SegmentSpec) =>
    api.post<EvaluateResult>("/audience/segments/evaluate", spec),
  size: (spec: SegmentSpec) =>
    api.post<{ size: number }>("/audience/segments/size", spec),
  compile: (spec: SegmentSpec) =>
    api.post<{ sql: string }>("/audience/segments/compile", spec),
  nl2sql: (text: string) => api.post<NL2SQLResult>("/audience/nl2sql", { text }),
  templates: () => api.get<{ templates: string[] }>("/audience/templates"),
};

// Campaign (M3 + M1)
export interface CampaignVariant {
  name: string;
  weight: number;
  content_id: string;
}
export interface CampaignRunRequest {
  id: string;
  audience_spec: SegmentSpec;
  channel: string;
  variants: CampaignVariant[];
  control_pct?: number;
  schedule?: { start?: string; end?: string; trigger_type?: string; trigger_event?: string };
  daily_cap?: number;
  triggered_users?: string[];
}
export const campaignApi = {
  run: (req: CampaignRunRequest) => api.post<any>("/campaign/campaigns/run", req),
};

// Content (M6)
export const contentApi = {
  generate: (body: { goal: string; product: string; locales: string[]; n?: number; channel?: string; tone?: string }) =>
    api.post<any>("/content/copy/generate", body),
  compliance: (body: { text: string; channel?: string; product?: string }) =>
    api.post<any>("/content/copy/compliance", body),
  selectBest: (records: any[]) => api.post<any>("/content/copy/select-best", { records }),
};

// Analytics (M4 + M9)
export const analyticsApi = {
  funnel: (body: { steps: string[]; within_days?: number; cross_product?: boolean }) =>
    api.post<any>("/analytics/funnel", body),
  attribution: (body: { records: any[]; conversions: any[]; window_hours?: number; model?: string }) =>
    api.post<any>("/analytics/attribution", body),
  report: (name: string, body: Record<string, unknown> = {}) =>
    api.post<any>(`/analytics/reports/${name}`, body),
  insights: (body: { series: number[]; labels?: string[]; z_threshold?: number }) =>
    api.post<any>("/analytics/insights", body),
};

// Personalization (M5)
export interface VariationIn {
  name: string;
  weight: number;
  payload: Record<string, unknown>;
}
export const personalizationApi = {
  register: (body: { key: string; audience_spec: SegmentSpec; variations: VariationIn[]; control_pct?: number }) =>
    api.post<any>("/personalize/experiences", body),
  publish: (key: string) => api.post<any>(`/personalize/experiences/${key}/publish`),
  fetch: (body: { identifiers: Record<string, string>; experience_keys: string[]; locale?: string }) =>
    api.post<{ experiences: Record<string, unknown> }>("/personalize/experiences/fetch", body),
};

// Experiment (M7)
export const experimentApi = {
  split: (body: { customer_ids: string[]; shadow_pct?: number }) =>
    api.post<any>("/experiment/shadow/split", body),
  report: (body: { control_records: any[]; shadow_records: any[]; non_inferiority_margin?: number }) =>
    api.post<any>("/experiment/shadow/report", body),
};

// Data platform (M8)
export const dataApi = {
  resolve: (identifiers: Record<string, string>) =>
    api.post<any>("/data/identity/resolve", { identifiers }),
  suppressionCheck: (customer_ids: string[]) =>
    api.post<any>("/data/suppression/check", { customer_ids }),
  ingest: (events: any[]) => api.post<any>("/data/ingest", { events }),
  dqc: () => api.get<any>("/data/dqc"),
};
