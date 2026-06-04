import { describe, it, expect } from "vitest";
import type { RuleGroupType } from "react-querybuilder";
import type { EventCondition, GroupNode, RuleNode } from "../../api/types";
import {
  dslToQuery,
  queryToDsl,
  qbOperatorToAttr,
  attrOperatorToQb,
} from "./dsl";

describe("operator mapping", () => {
  const pairs: Array<[string, string]> = [
    ["=", "eq"],
    ["!=", "ne"],
    ["<", "lt"],
    ["<=", "lte"],
    [">", "gt"],
    [">=", "gte"],
    ["in", "in"],
    ["notIn", "not_in"],
    ["between", "between"],
    ["contains", "contains"],
    ["notNull", "exists"],
    ["null", "not_exists"],
  ];

  it.each(pairs)("maps qb '%s' <-> attr '%s' both ways", (qb, attr) => {
    expect(qbOperatorToAttr(qb)).toBe(attr);
    expect(attrOperatorToQb(attr as never)).toBe(qb);
  });
});

describe("queryToDsl", () => {
  it("maps combinator and a value rule to an attribute node", () => {
    const query: RuleGroupType = {
      combinator: "and",
      rules: [{ field: "balance", operator: ">", value: "100" }],
    };
    expect(queryToDsl(query)).toEqual<RuleNode>({
      op: "and",
      children: [{ type: "attribute", field: "balance", operator: "gt", value: 100 }],
    });
  });

  it("maps the `not` flag to a NOT group wrapper", () => {
    const query: RuleGroupType = {
      combinator: "or",
      not: true,
      rules: [{ field: "country", operator: "=", value: "UAE" }],
    };
    expect(queryToDsl(query)).toEqual<RuleNode>({
      op: "not",
      children: [
        {
          op: "or",
          children: [{ type: "attribute", field: "country", operator: "eq", value: "UAE" }],
        },
      ],
    });
  });

  it("drops the value for valueless operators (exists/not_exists)", () => {
    const query: RuleGroupType = {
      combinator: "and",
      rules: [{ field: "is_kyc", operator: "notNull", value: "" }],
    };
    expect(queryToDsl(query)).toEqual<RuleNode>({
      op: "and",
      children: [{ type: "attribute", field: "is_kyc", operator: "exists" }],
    });
  });

  it("parses comma strings into lists for in/between", () => {
    const query: RuleGroupType = {
      combinator: "and",
      rules: [
        { field: "country", operator: "in", value: "UAE,KSA" },
        { field: "balance", operator: "between", value: "10,20" },
      ],
    };
    expect(queryToDsl(query)).toEqual<RuleNode>({
      op: "and",
      children: [
        { type: "attribute", field: "country", operator: "in", value: ["UAE", "KSA"] },
        { type: "attribute", field: "balance", operator: "between", value: [10, 20] },
      ],
    });
  });
});

describe("round-trip queryToDsl(dslToQuery(x)) === x", () => {
  it("round-trips a nested and/or DSL", () => {
    const dsl: GroupNode = {
      op: "and",
      children: [
        { type: "attribute", field: "is_kyc", operator: "eq", value: true },
        {
          op: "or",
          children: [
            { type: "attribute", field: "country", operator: "in", value: ["UAE", "KSA"] },
            { type: "attribute", field: "balance", operator: "between", value: [100, 500] },
          ],
        },
      ],
    };
    expect(queryToDsl(dslToQuery(dsl))).toEqual(dsl);
  });

  it("round-trips a NOT group", () => {
    const dsl: GroupNode = {
      op: "not",
      children: [
        {
          op: "and",
          children: [
            { type: "attribute", field: "wallet_activated", operator: "eq", value: true },
          ],
        },
      ],
    };
    expect(queryToDsl(dslToQuery(dsl))).toEqual(dsl);
  });

  it("covers every attribute operator in a round-trip", () => {
    const dsl: GroupNode = {
      op: "and",
      children: [
        { type: "attribute", field: "a", operator: "eq", value: 1 },
        { type: "attribute", field: "b", operator: "ne", value: 2 },
        { type: "attribute", field: "c", operator: "lt", value: 3 },
        { type: "attribute", field: "d", operator: "lte", value: 4 },
        { type: "attribute", field: "e", operator: "gt", value: 5 },
        { type: "attribute", field: "f", operator: "gte", value: 6 },
        { type: "attribute", field: "g", operator: "in", value: [1, 2] },
        { type: "attribute", field: "h", operator: "not_in", value: [3, 4] },
        { type: "attribute", field: "i", operator: "between", value: [5, 6] },
        { type: "attribute", field: "j", operator: "contains", value: "x" },
        { type: "attribute", field: "k", operator: "exists" },
        { type: "attribute", field: "l", operator: "not_exists" },
      ],
    };
    expect(queryToDsl(dslToQuery(dsl))).toEqual(dsl);
  });
});

describe("event nodes survive a round-trip (lossless stash)", () => {
  it("keeps an event condition through dslToQuery -> queryToDsl", () => {
    const event: EventCondition = {
      type: "event",
      event: "money_transfer",
      frequency: { op: "at_least", value: 3 },
      within_days: 30,
      where: {
        type: "attribute",
        field: "amount",
        operator: "gt",
        value: 100,
      },
    };
    const dsl: GroupNode = {
      op: "and",
      children: [
        { type: "attribute", field: "is_kyc", operator: "eq", value: true },
        event,
      ],
    };
    const roundTripped = queryToDsl(dslToQuery(dsl));
    expect(roundTripped).toEqual(dsl);
  });
});
