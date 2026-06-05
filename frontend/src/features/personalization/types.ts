// Local types + helpers for the Personalization (M5 / 千人千面) screen.
import type { SegmentSpec } from "../../api/types";
import type { VariationIn } from "../../api/client";

// Botim markets — the per-locale payload editor produces one bucket per locale.
export const LOCALES = ["en", "ar", "hi", "tl"] as const;
export type Locale = (typeof LOCALES)[number];

// One editable key/value pair inside a single locale bucket.
export interface KVRow {
  key: string;
  k: string;
  v: string;
}

// Per-locale buckets of key/value rows. Assembled into payload like
// { en: {title: "Hi"}, ar: {title: "..."} } — empty locales are dropped.
export type LocalePayload = Record<Locale, KVRow[]>;

// An editable variation row in the New-experience form.
export interface VariationRow {
  key: string;
  name: string;
  weight: number;
  payload: LocalePayload;
}

// A registered experience tracked in-memory for this session.
export interface ExperienceItem {
  key: string;
  variations: number;
  control_pct: number;
  status: "draft" | "published";
}

export function emptyLocalePayload(): LocalePayload {
  return { en: [], ar: [], hi: [], tl: [] };
}

// Assemble the per-locale KV editor state into the API `payload` shape:
// { en: {k: v, ...}, ar: {...} }. Locales with no non-empty rows are omitted.
export function assemblePayload(lp: LocalePayload): Record<string, unknown> {
  const out: Record<string, Record<string, string>> = {};
  for (const locale of LOCALES) {
    const bucket: Record<string, string> = {};
    for (const row of lp[locale]) {
      if (row.k.trim()) bucket[row.k.trim()] = row.v;
    }
    if (Object.keys(bucket).length > 0) out[locale] = bucket;
  }
  return out;
}

export function toVariationIn(rows: VariationRow[]): VariationIn[] {
  return rows.map((r) => ({
    name: r.name,
    weight: r.weight,
    payload: assemblePayload(r.payload),
  }));
}

// Default audience spec — KYC-verified users (per the M5 default in the spec).
export const DEFAULT_AUDIENCE: SegmentSpec = {
  name: "KYC users",
  match: { type: "attribute", field: "kyc_verified", operator: "eq", value: true },
};

export function defaultAudienceJson(): string {
  return JSON.stringify(DEFAULT_AUDIENCE, null, 2);
}

export interface ParsedAudience {
  spec: SegmentSpec | null;
  error: string | null;
}

export function parseAudience(json: string): ParsedAudience {
  try {
    const spec = JSON.parse(json) as SegmentSpec;
    if (!spec || typeof spec !== "object" || !("match" in spec)) {
      return { spec: null, error: "Audience spec must be an object with a `match` rule." };
    }
    return { spec, error: null };
  } catch (e) {
    return { spec: null, error: e instanceof Error ? e.message : "Invalid JSON." };
  }
}

let seq = 0;
export function nextKey(prefix = "row"): string {
  seq += 1;
  return `${prefix}_${Date.now()}_${seq}`;
}

export function defaultVariationRow(name: string): VariationRow {
  return { key: nextKey("var"), name, weight: 1, payload: emptyLocalePayload() };
}

export interface VariationsValidation {
  ok: boolean;
  message?: string;
}

export function validateVariations(rows: VariationRow[]): VariationsValidation {
  if (rows.length === 0) return { ok: false, message: "Add at least one variation." };
  if (rows.some((r) => !r.name.trim())) {
    return { ok: false, message: "Every variation needs a name." };
  }
  if (rows.reduce((a, r) => a + r.weight, 0) <= 0) {
    return { ok: false, message: "Total weight must be greater than 0." };
  }
  return { ok: true };
}
