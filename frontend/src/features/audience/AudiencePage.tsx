// Audience (M2 Cohort Segmentation) screen.
//
// - NL2SQL panel: plain-language -> audienceApi.nl2sql -> load DSL into builder.
// - Rule builder: react-querybuilder bound bidirectionally to the M2 DSL.
// - Real-time size estimate: debounced audienceApi.size on every builder change.
// - Templates: audienceApi.templates (names only).
// - DSL preview + optional Compile SQL.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  Col,
  Input,
  List,
  Row,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
  message,
} from "antd";
import { QueryBuilder, type Field, type RuleGroupType } from "react-querybuilder";
import "react-querybuilder/dist/query-builder.css";

import { audienceApi } from "../../api/client";
import type { SegmentSpec } from "../../api/types";
import { dslToQuery, queryToDsl } from "./dsl";

const { Title, Paragraph, Text } = Typography;

// Fields exposed in the visual rule builder. Operators are restricted to ones
// the M2 DSL understands (see dsl.ts operator mapping).
const NUMERIC_OPERATORS = [
  { name: "=", label: "=" },
  { name: "!=", label: "!=" },
  { name: "<", label: "<" },
  { name: "<=", label: "<=" },
  { name: ">", label: ">" },
  { name: ">=", label: ">=" },
  { name: "between", label: "between" },
  { name: "in", label: "in" },
  { name: "notIn", label: "not in" },
  { name: "notNull", label: "exists" },
  { name: "null", label: "not exists" },
];

const STRING_OPERATORS = [
  { name: "=", label: "=" },
  { name: "!=", label: "!=" },
  { name: "contains", label: "contains" },
  { name: "in", label: "in" },
  { name: "notIn", label: "not in" },
  { name: "notNull", label: "exists" },
  { name: "null", label: "not exists" },
];

const BOOL_OPERATORS = [
  { name: "=", label: "=" },
  { name: "!=", label: "!=" },
  { name: "notNull", label: "exists" },
];

const fields: Field[] = [
  { name: "is_kyc", label: "Is KYC", operators: BOOL_OPERATORS, defaultValue: "true" },
  {
    name: "wallet_activated",
    label: "Wallet activated",
    operators: BOOL_OPERATORS,
    defaultValue: "true",
  },
  { name: "balance", label: "Balance", inputType: "number", operators: NUMERIC_OPERATORS },
  { name: "country", label: "Country", operators: STRING_OPERATORS },
  {
    name: "device_height",
    label: "Device height",
    inputType: "number",
    operators: NUMERIC_OPERATORS,
  },
  { name: "platform", label: "Platform", operators: STRING_OPERATORS },
];

const EMPTY_QUERY: RuleGroupType = { combinator: "and", rules: [] };

export default function AudiencePage() {
  const { t } = useTranslation();

  const [query, setQuery] = useState<RuleGroupType>(EMPTY_QUERY);

  // NL2SQL state
  const [nlText, setNlText] = useState("");
  const [nlLoading, setNlLoading] = useState(false);
  const [nlConfidence, setNlConfidence] = useState<number | null>(null);
  const [nlRequiresReview, setNlRequiresReview] = useState(false);

  // Size estimate state
  const [size, setSize] = useState<number | null>(null);
  const [sizeLoading, setSizeLoading] = useState(false);
  const [sizeError, setSizeError] = useState<string | null>(null);

  // Templates
  const [templates, setTemplates] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  // Compile SQL
  const [sql, setSql] = useState<string | null>(null);
  const [sqlLoading, setSqlLoading] = useState(false);

  // The computed SegmentSpec derived from the builder query.
  const spec: SegmentSpec = useMemo(
    () => ({ name: selectedTemplate ?? "audience-segment", match: queryToDsl(query) }),
    [query, selectedTemplate],
  );

  // --- NL2SQL ---------------------------------------------------------------
  const handleTranslate = useCallback(async () => {
    if (!nlText.trim()) return;
    setNlLoading(true);
    try {
      const result = await audienceApi.nl2sql(nlText);
      setNlConfidence(result.confidence);
      setNlRequiresReview(result.requires_review);
      // Load the produced DSL into the builder (round-trips via dslToQuery).
      setQuery(dslToQuery(result.dsl.match));
    } catch (e) {
      message.error(`Translate failed: ${(e as Error).message}`);
    } finally {
      setNlLoading(false);
    }
  }, [nlText]);

  // --- Templates ------------------------------------------------------------
  useEffect(() => {
    let alive = true;
    audienceApi
      .templates()
      .then((res) => {
        if (alive) setTemplates(res.templates ?? []);
      })
      .catch((e) => message.error(`Templates failed: ${(e as Error).message}`));
    return () => {
      alive = false;
    };
  }, []);

  // --- Real-time size estimate (debounced) ----------------------------------
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    // Skip estimation for an empty query (no rules to size).
    if (!spec.match || (spec.match as { children?: unknown[] }).children?.length === 0) {
      setSize(null);
      setSizeError(null);
      return;
    }
    // `alive` is scoped to the effect (not the setTimeout callback) so the real
    // cleanup below can cancel a stale in-flight response from setting state.
    let alive = true;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSizeLoading(true);
      setSizeError(null);
      audienceApi
        .size(spec)
        .then((res) => {
          if (alive) setSize(res.size);
        })
        .catch((e) => {
          if (alive) {
            setSizeError((e as Error).message);
            setSize(null);
          }
        })
        .finally(() => {
          if (alive) setSizeLoading(false);
        });
    }, 400);
    return () => {
      alive = false;
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [spec]);

  // --- Compile SQL ----------------------------------------------------------
  const handleCompile = useCallback(async () => {
    setSqlLoading(true);
    try {
      const res = await audienceApi.compile(spec);
      setSql(res.sql);
    } catch (e) {
      message.error(`Compile failed: ${(e as Error).message}`);
    } finally {
      setSqlLoading(false);
    }
  }, [spec]);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Title level={3}>{t("audience.title")}</Title>

      <Row gutter={16}>
        <Col xs={24} lg={16}>
          {/* NL2SQL panel */}
          <Card title={t("audience.nl")} size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Input.TextArea
                aria-label="nl2sql-input"
                rows={3}
                value={nlText}
                onChange={(e) => setNlText(e.target.value)}
                placeholder="e.g. KYC users in UAE with balance over 100"
              />
              <Space>
                <Button
                  type="primary"
                  loading={nlLoading}
                  onClick={handleTranslate}
                  disabled={!nlText.trim()}
                >
                  {t("audience.translate")}
                </Button>
                {nlConfidence !== null && (
                  <Text data-testid="nl-confidence">
                    Confidence: {(nlConfidence * 100).toFixed(0)}%
                  </Text>
                )}
                {nlRequiresReview && <Tag color="warning">{t("audience.review")}</Tag>}
              </Space>
            </Space>
          </Card>

          {/* Rule builder */}
          <Card title="Rule builder" size="small" style={{ marginBottom: 16 }}>
            <QueryBuilder
              fields={fields}
              query={query}
              onQueryChange={(q) => setQuery(q as RuleGroupType)}
            />
          </Card>

          {/* DSL preview */}
          <Card title={t("audience.dsl")} size="small">
            <Space direction="vertical" style={{ width: "100%" }}>
              <pre
                data-testid="dsl-preview"
                style={{
                  margin: 0,
                  maxHeight: 280,
                  overflow: "auto",
                  background: "#f6f6f6",
                  padding: 12,
                  borderRadius: 4,
                }}
              >
                {JSON.stringify(spec, null, 2)}
              </pre>
              <Space>
                <Button onClick={handleCompile} loading={sqlLoading}>
                  Compile SQL
                </Button>
              </Space>
              {sql && (
                <pre
                  data-testid="sql-preview"
                  style={{
                    margin: 0,
                    maxHeight: 240,
                    overflow: "auto",
                    background: "#1e1e1e",
                    color: "#d4d4d4",
                    padding: 12,
                    borderRadius: 4,
                  }}
                >
                  {sql}
                </pre>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* Real-time size estimate */}
          <Card size="small" style={{ marginBottom: 16 }}>
            {sizeLoading ? (
              <Spin />
            ) : (
              <Statistic
                title={t("audience.size")}
                value={size ?? 0}
                data-testid="audience-size"
              />
            )}
            {sizeError && (
              <Alert
                type="error"
                showIcon
                style={{ marginTop: 8 }}
                message="Size estimate failed"
                description={sizeError}
              />
            )}
          </Card>

          {/* Templates */}
          <Card title="Templates" size="small">
            <List
              size="small"
              dataSource={templates}
              locale={{ emptyText: "No templates" }}
              renderItem={(name) => (
                <List.Item
                  onClick={() => setSelectedTemplate(name)}
                  style={{
                    cursor: "pointer",
                    fontWeight: selectedTemplate === name ? 600 : 400,
                  }}
                >
                  {name}
                </List.Item>
              )}
            />
            {selectedTemplate && (
              <Paragraph style={{ marginTop: 8 }}>
                Selected: <Text strong>{selectedTemplate}</Text>
              </Paragraph>
            )}
          </Card>
        </Col>
      </Row>
    </Space>
  );
}
