// Local wizard state types for the Campaign 3-step wizard.
import type { CampaignVariant, CampaignRunRequest } from "../../api/client";
import type { SegmentSpec } from "../../api/types";

export type TriggerType = "batch" | "triggered";

// A variant row in the editable table. Carries a stable key for AntD row identity
// (the user-facing `name` may be edited / temporarily empty).
export interface VariantRow extends CampaignVariant {
  key: string;
}

export interface WizardState {
  // Step 1 — audience
  audienceJson: string; // raw JSON the user edits; parsed to SegmentSpec on demand
  estimatedSize: number | null;
  // Step 2 — content
  variants: VariantRow[];
  controlPct: number; // 0..1
  // Step 3 — schedule & goals
  channel: string;
  start: string | null; // ISO string
  end: string | null; // ISO string
  triggerType: TriggerType;
  triggerEvent: string;
  dailyCap: number;
}

// A sensible pre-filled audience: KYC-verified users.
export const DEFAULT_AUDIENCE_SPEC: SegmentSpec = {
  name: "KYC verified users",
  match: {
    type: "attribute",
    field: "kyc_status",
    operator: "eq",
    value: "verified",
  },
};

export function defaultWizardState(): WizardState {
  return {
    audienceJson: JSON.stringify(DEFAULT_AUDIENCE_SPEC, null, 2),
    estimatedSize: null,
    variants: [
      { key: "v1", name: "A", weight: 1, content_id: "content_a" },
      { key: "v2", name: "B", weight: 1, content_id: "content_b" },
    ],
    controlPct: 0.1,
    channel: "push",
    start: null,
    end: null,
    triggerType: "batch",
    triggerEvent: "",
    dailyCap: 1,
  };
}

export interface ValidationResult {
  ok: boolean;
  message?: string;
}

export function validateVariants(variants: VariantRow[]): ValidationResult {
  if (variants.length === 0) {
    return { ok: false, message: "Add at least one variant." };
  }
  if (variants.some((v) => !v.name.trim())) {
    return { ok: false, message: "Every variant needs a name." };
  }
  const names = variants.map((v) => v.name.trim());
  if (new Set(names).size !== names.length) {
    return { ok: false, message: "Variant names must be unique." };
  }
  if (names.includes("control")) {
    return { ok: false, message: "'control' is a reserved variant name." };
  }
  if (variants.some((v) => !(v.weight > 0))) {
    return { ok: false, message: "All variant weights must be greater than 0." };
  }
  return { ok: true };
}

export function parseAudience(json: string): { spec?: SegmentSpec; error?: string } {
  try {
    const spec = JSON.parse(json) as SegmentSpec;
    if (!spec || typeof spec !== "object" || !spec.match) {
      return { error: "Audience spec must be an object with a 'match' rule." };
    }
    return { spec };
  } catch {
    return { error: "Audience spec is not valid JSON." };
  }
}

// Assemble the request payload sent to campaignApi.run.
export function buildRunRequest(state: WizardState): CampaignRunRequest {
  const { spec } = parseAudience(state.audienceJson);
  return {
    id: `cmp_${Date.now()}`,
    audience_spec: spec as SegmentSpec,
    channel: state.channel,
    variants: state.variants.map(({ name, weight, content_id }) => ({
      name: name.trim(),
      weight,
      content_id,
    })),
    control_pct: state.controlPct,
    schedule: {
      start: state.start ?? undefined,
      end: state.end ?? undefined,
      trigger_type: state.triggerType,
      trigger_event:
        state.triggerType === "triggered" ? state.triggerEvent || undefined : undefined,
    },
    daily_cap: state.dailyCap,
  };
}
