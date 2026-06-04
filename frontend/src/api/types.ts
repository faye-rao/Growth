// Rule DSL types — mirror the backend M2 cohort_engine JSON DSL.
// The Audience rule builder must map react-querybuilder <-> these types both ways.

export type AttrOperator =
  | "eq" | "ne" | "gt" | "gte" | "lt" | "lte"
  | "in" | "not_in" | "exists" | "not_exists" | "between" | "contains";

export type FreqOp = "at_least" | "at_most" | "exactly" | "min_percent" | "predominantly";
export type GroupOp = "and" | "or" | "not";

export interface AttributeCondition {
  type: "attribute";
  field: string;
  operator: AttrOperator;
  value?: unknown;
}

export interface Frequency {
  op: FreqOp;
  value?: number;
}

export interface EventCondition {
  type: "event";
  event: string;
  frequency: Frequency;
  within_days?: number;
  where?: RuleNode;
}

export interface GroupNode {
  op: GroupOp;
  children: RuleNode[];
}

export type RuleNode = AttributeCondition | EventCondition | GroupNode;

export interface SegmentSpec {
  name?: string;
  match: RuleNode;
  exclude?: RuleNode;
}

export interface NL2SQLResult {
  text: string;
  dsl: { match: RuleNode; exclude?: RuleNode };
  confidence: number;
  matched: string[];
  unmatched: string[];
  requires_review: boolean;
}

export interface EvaluateResult {
  size: number;
  customer_ids: string[];
}
