// Bidirectional mapping between react-querybuilder's RuleGroupType and the M2
// cohort DSL RuleNode (see src/api/types.ts and the backend cohort_engine).
//
// Core requirement (frontend/CLAUDE.md): the rule builder must map BOTH ways so
// that a DSL produced by NL2SQL (or loaded from a template) round-trips and
// renders, and the builder's output can be compiled/evaluated by the backend.
//
// - combinator and/or  <-> group op and/or
// - `not` flag         <-> group op "not"
// - rule               <-> {type:"attribute", field, operator, value}
// - event nodes (not editable in the visual builder) are stashed LOSSLESSLY in a
//   sentinel rule so they survive a dslToQuery -> queryToDsl round-trip.

import type { RuleGroupType, RuleType } from "react-querybuilder";
import type {
  AttrOperator,
  AttributeCondition,
  EventCondition,
  GroupNode,
  RuleNode,
} from "../../api/types";

// --- operator mapping (querybuilder <-> M2 AttrOperator) ----------------------

// querybuilder operator name -> M2 AttrOperator
const QB_TO_ATTR: Record<string, AttrOperator> = {
  "=": "eq",
  "!=": "ne",
  "<": "lt",
  "<=": "lte",
  ">": "gt",
  ">=": "gte",
  in: "in",
  notIn: "not_in",
  between: "between",
  contains: "contains",
  notNull: "exists",
  null: "not_exists",
};

// M2 AttrOperator -> querybuilder operator name (inverse of QB_TO_ATTR)
const ATTR_TO_QB: Record<AttrOperator, string> = {
  eq: "=",
  ne: "!=",
  lt: "<",
  lte: "<=",
  gt: ">",
  gte: ">=",
  in: "in",
  not_in: "notIn",
  between: "between",
  contains: "contains",
  exists: "notNull",
  not_exists: "null",
};

// Operators that carry no value in the M2 DSL.
const VALUELESS: ReadonlySet<AttrOperator> = new Set(["exists", "not_exists"]);
// Operators whose value is a list ("in"/"not_in") or a 2-tuple ("between").
const LIST_OPS: ReadonlySet<AttrOperator> = new Set(["in", "not_in"]);

// Sentinel field name used to stash a non-attribute node (e.g. an event
// condition) inside a querybuilder rule without losing information.
export const RAW_NODE_FIELD = "__rawNode";
export const RAW_NODE_OPERATOR = "__raw";

export function qbOperatorToAttr(op: string): AttrOperator {
  const mapped = QB_TO_ATTR[op];
  if (!mapped) throw new Error(`unsupported querybuilder operator: ${op}`);
  return mapped;
}

export function attrOperatorToQb(op: AttrOperator): string {
  const mapped = ATTR_TO_QB[op];
  if (!mapped) throw new Error(`unsupported attribute operator: ${op}`);
  return mapped;
}

// --- value (de)serialization between querybuilder strings and DSL values ------

// querybuilder typically stores list/between values as comma-joined strings.
function qbValueToDslValue(operator: AttrOperator, value: unknown): unknown {
  if (VALUELESS.has(operator)) return undefined;
  if (LIST_OPS.has(operator) || operator === "between") {
    const arr = toArray(value);
    return arr.map(coerceScalar);
  }
  return coerceScalar(value);
}

function dslValueToQbValue(operator: AttrOperator, value: unknown): unknown {
  if (VALUELESS.has(operator)) return undefined;
  if (LIST_OPS.has(operator) || operator === "between") {
    const arr = Array.isArray(value) ? value : toArray(value);
    return arr.join(",");
  }
  return value;
}

function toArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null || value === "") return [];
  return String(value)
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

// Coerce a querybuilder string into number/boolean when it looks like one, so a
// builder-entered "42" maps to the numeric 42 the backend expects.
function coerceScalar(value: unknown): unknown {
  if (typeof value !== "string") return value;
  const t = value.trim();
  if (t === "") return value;
  if (t === "true") return true;
  if (t === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(t)) return Number(t);
  return value;
}

// --- querybuilder -> DSL ------------------------------------------------------

export function queryToDsl(query: RuleGroupType): RuleNode {
  return groupToDsl(query);
}

function groupToDsl(group: RuleGroupType): RuleNode {
  const children: RuleNode[] = group.rules
    // skip the placeholder empty rule react-querybuilder may create
    .filter((r) => !isEmptyPlaceholder(r))
    .map((r) =>
      "rules" in r ? groupToDsl(r as RuleGroupType) : ruleToDsl(r as RuleType),
    );

  const combinator = (group.combinator || "and").toLowerCase();
  const op = combinator === "or" ? "or" : "and";

  const inner: GroupNode = { op, children };

  if (group.not) {
    // A `not` flag wraps the group's AND/OR composition in a NOT group.
    return { op: "not", children: [inner] };
  }
  return inner;
}

function ruleToDsl(rule: RuleType): RuleNode {
  // A stashed raw (non-attribute) node round-trips verbatim.
  if (rule.field === RAW_NODE_FIELD) {
    return decodeRawNode(rule.value) as RuleNode;
  }

  const operator = qbOperatorToAttr(rule.operator);
  const cond: AttributeCondition = {
    type: "attribute",
    field: rule.field,
    operator,
  };
  const value = qbValueToDslValue(operator, rule.value);
  if (value !== undefined) cond.value = value;
  return cond;
}

function isEmptyPlaceholder(r: RuleType | RuleGroupType): boolean {
  if ("rules" in r) return false;
  const rule = r as RuleType;
  return !rule.field && !rule.operator;
}

// --- DSL -> querybuilder ------------------------------------------------------

export function dslToQuery(node: RuleNode): RuleGroupType {
  // Ensure the top level is always a group so <QueryBuilder> can render it.
  if (isGroup(node)) {
    return groupToQuery(node);
  }
  // A bare attribute/event node becomes a single-rule AND group.
  return { combinator: "and", rules: [nodeToRuleOrGroup(node)] };
}

function groupToQuery(group: GroupNode): RuleGroupType {
  // A "not" group with a single group child collapses back into that child with
  // the `not` flag set (inverse of groupToDsl's NOT wrapping).
  if (group.op === "not") {
    if (group.children.length === 1 && isGroup(group.children[0])) {
      const child = groupToQuery(group.children[0] as GroupNode);
      return { ...child, not: true };
    }
    // General NOT (e.g. wrapping a single attribute/event): keep as an AND group
    // marked `not`.
    return {
      combinator: "and",
      not: true,
      rules: group.children.map(nodeToRuleOrGroup),
    };
  }

  return {
    combinator: group.op, // "and" | "or"
    rules: group.children.map(nodeToRuleOrGroup),
  };
}

function nodeToRuleOrGroup(node: RuleNode): RuleType | RuleGroupType {
  if (isGroup(node)) return groupToQuery(node);
  if (isAttribute(node)) return attributeToRule(node);
  // Event (or any non-attribute leaf) is stashed losslessly as a sentinel rule.
  return rawNodeToRule(node as EventCondition);
}

function attributeToRule(node: AttributeCondition): RuleType {
  return {
    field: node.field,
    operator: attrOperatorToQb(node.operator),
    value: dslValueToQbValue(node.operator, node.value),
  };
}

function rawNodeToRule(node: RuleNode): RuleType {
  return {
    field: RAW_NODE_FIELD,
    operator: RAW_NODE_OPERATOR,
    value: encodeRawNode(node),
  };
}

// --- raw-node stash (lossless) ------------------------------------------------

function encodeRawNode(node: RuleNode): string {
  return JSON.stringify(node);
}

function decodeRawNode(value: unknown): RuleNode {
  if (typeof value === "string") return JSON.parse(value) as RuleNode;
  // Already an object (defensive): clone to avoid shared references.
  return JSON.parse(JSON.stringify(value)) as RuleNode;
}

// --- type guards --------------------------------------------------------------

function isGroup(node: RuleNode): node is GroupNode {
  return (node as GroupNode).op !== undefined && "children" in node;
}

function isAttribute(node: RuleNode): node is AttributeCondition {
  return (node as AttributeCondition).type === "attribute";
}
