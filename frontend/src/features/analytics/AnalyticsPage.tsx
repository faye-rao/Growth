import { useState } from "react";
import { useTranslation } from "react-i18next";
import ReactECharts from "echarts-for-react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Divider,
  Empty,
  Input,
  InputNumber,
  List,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";

import { analyticsApi, ApiError } from "../../api/client";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

// ---- backend response shapes (mirrors src/services/analytics.py) -------------

interface FunnelResult {
  steps: string[];
  step_counts: number[];
  step_conversion: number[];
  drop_off: number[];
  overall_conversion: number;
}

interface AttributionResult {
  model: string;
  conversions_per_campaign: Record<string, number>;
  sent_per_campaign: Record<string, number>;
  conversion_rate_per_campaign: Record<string, number>;
  total_conversions: number;
  unattributed: number;
}

interface Insight {
  index: number;
  label: string;
  value: number;
  direction: string;
  z_score: number;
  pct_change: number | null;
  notable: boolean;
  narrative: string;
}

const REPORT_NAMES = [
  "active_users",
  "new_vs_returning",
  "event_volume",
  "retention_lite",
] as const;
type ReportName = (typeof REPORT_NAMES)[number];

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return String(e);
}

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

// ---- Funnel panel ------------------------------------------------------------

function FunnelPanel() {
  const [steps, setSteps] = useState<string[]>(["App Opened", "Transfer"]);
  const [withinDays, setWithinDays] = useState<number | null>(null);
  const [crossProduct, setCrossProduct] = useState(false);
  const [result, setResult] = useState<FunnelResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setStep = (i: number, v: string) =>
    setSteps((s) => s.map((x, k) => (k === i ? v : x)));
  const addStep = () => setSteps((s) => [...s, ""]);
  const removeStep = (i: number) =>
    setSteps((s) => s.filter((_, k) => k !== i));

  async function run() {
    const cleaned = steps.map((s) => s.trim()).filter(Boolean);
    if (cleaned.length === 0) {
      setError("Add at least one funnel step.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.funnel({
        steps: cleaned,
        within_days: withinDays ?? undefined,
        cross_product: crossProduct,
      });
      setResult(res as FunnelResult);
    } catch (e) {
      setError(errMsg(e));
      message.error("Funnel computation failed");
    } finally {
      setLoading(false);
    }
  }

  const chartOption = result
    ? {
        tooltip: { trigger: "item", formatter: "{b}: {c}" },
        series: [
          {
            type: "funnel",
            sort: "none",
            label: { show: true, position: "inside" },
            data: result.steps.map((name, i) => ({
              name,
              value: result.step_counts[i],
            })),
          },
        ],
      }
    : null;

  const rows = result
    ? result.steps.map((name, i) => ({
        key: i,
        step: name,
        count: result.step_counts[i],
        conversion: pct(result.step_conversion[i]),
        drop: result.drop_off[i],
      }))
    : [];

  return (
    <Card>
      <Title level={4}>Funnel</Title>
      <Paragraph type="secondary">
        Ordered, in-sequence conversion funnel. Toggle cross-product to stitch a
        journey across Botim product lines.
      </Paragraph>

      <Space direction="vertical" style={{ width: "100%" }} size="small">
        {steps.map((s, i) => (
          <Space key={i}>
            <Text style={{ width: 24, display: "inline-block" }}>{i + 1}.</Text>
            <Input
              aria-label={`funnel-step-${i}`}
              placeholder="Event name"
              value={s}
              style={{ width: 260 }}
              onChange={(e) => setStep(i, e.target.value)}
            />
            <Button
              aria-label={`remove-step-${i}`}
              icon={<DeleteOutlined />}
              onClick={() => removeStep(i)}
              disabled={steps.length <= 1}
            />
          </Space>
        ))}
        <Button icon={<PlusOutlined />} onClick={addStep}>
          Add step
        </Button>
      </Space>

      <Divider />

      <Space wrap>
        <span>
          <Text>within_days: </Text>
          <InputNumber
            aria-label="within-days"
            min={1}
            value={withinDays}
            placeholder="(any)"
            onChange={(v) => setWithinDays(v ?? null)}
          />
        </span>
        <Checkbox
          checked={crossProduct}
          onChange={(e) => setCrossProduct(e.target.checked)}
        >
          cross-product
        </Checkbox>
        <Button type="primary" loading={loading} onClick={run}>
          Compute funnel
        </Button>
      </Space>

      {error && (
        <Alert
          style={{ marginTop: 16 }}
          type="error"
          showIcon
          message={error}
        />
      )}

      {result && (
        <>
          <Divider />
          <Statistic
            title="Overall conversion"
            value={pct(result.overall_conversion)}
          />
          {chartOption && (
            <ReactECharts
              option={chartOption}
              style={{ height: 320 }}
              notMerge
            />
          )}
          <Table
            style={{ marginTop: 16 }}
            size="small"
            pagination={false}
            dataSource={rows}
            columns={[
              { title: "Step", dataIndex: "step", key: "step" },
              { title: "Users", dataIndex: "count", key: "count" },
              {
                title: "Conversion",
                dataIndex: "conversion",
                key: "conversion",
              },
              { title: "Drop-off", dataIndex: "drop", key: "drop" },
            ]}
          />
        </>
      )}
    </Card>
  );
}

// ---- Attribution panel -------------------------------------------------------

const SAMPLE_RECORDS = JSON.stringify(
  [
    {
      customer_id: "u1",
      campaign_id: "promo_a",
      channel: "push",
      content_id: "c1",
      ts: "2026-01-01T09:00:00",
    },
    {
      customer_id: "u2",
      campaign_id: "promo_b",
      channel: "push",
      content_id: "c2",
      ts: "2026-01-01T10:00:00",
    },
  ],
  null,
  2,
);

const SAMPLE_CONVERSIONS = JSON.stringify(
  [
    { customer_id: "u1", event_name: "Transfer", ts: "2026-01-01T11:00:00" },
    { customer_id: "u2", event_name: "Transfer", ts: "2026-01-01T12:00:00" },
  ],
  null,
  2,
);

function AttributionPanel() {
  const [recordsText, setRecordsText] = useState(SAMPLE_RECORDS);
  const [conversionsText, setConversionsText] = useState(SAMPLE_CONVERSIONS);
  const [windowHours, setWindowHours] = useState<number | null>(24);
  const [model, setModel] = useState<"last_touch" | "first_touch">(
    "last_touch",
  );
  const [result, setResult] = useState<AttributionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    let records: unknown;
    let conversions: unknown;
    try {
      records = JSON.parse(recordsText);
      conversions = JSON.parse(conversionsText);
    } catch {
      setError("Records / conversions must be valid JSON arrays.");
      return;
    }
    if (!Array.isArray(records) || !Array.isArray(conversions)) {
      setError("Records and conversions must both be JSON arrays.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.attribution({
        records,
        conversions,
        window_hours: windowHours ?? undefined,
        model,
      });
      setResult(res as AttributionResult);
    } catch (e) {
      setError(errMsg(e));
      message.error("Attribution failed");
    } finally {
      setLoading(false);
    }
  }

  const rows = result
    ? Object.keys(result.sent_per_campaign).map((cid) => ({
        key: cid,
        campaign: cid,
        sent: result.sent_per_campaign[cid],
        conversions: result.conversions_per_campaign[cid] ?? 0,
        rate: pct(result.conversion_rate_per_campaign[cid] ?? 0),
      }))
    : [];

  return (
    <Card>
      <Title level={4}>Attribution</Title>
      <Paragraph type="secondary">
        Credit conversions back to the campaigns that touched the user, within a
        window.
      </Paragraph>

      <Row gutter={16}>
        <Col span={12}>
          <Text>Delivery records (JSON)</Text>
          <TextArea
            aria-label="attribution-records"
            rows={8}
            value={recordsText}
            onChange={(e) => setRecordsText(e.target.value)}
          />
        </Col>
        <Col span={12}>
          <Text>Conversions (JSON)</Text>
          <TextArea
            aria-label="attribution-conversions"
            rows={8}
            value={conversionsText}
            onChange={(e) => setConversionsText(e.target.value)}
          />
        </Col>
      </Row>

      <Space style={{ marginTop: 16 }} wrap>
        <span>
          <Text>window_hours: </Text>
          <InputNumber
            aria-label="window-hours"
            min={0}
            value={windowHours}
            onChange={(v) => setWindowHours(v ?? null)}
          />
        </span>
        <span>
          <Text>model: </Text>
          <Select
            aria-label="attribution-model"
            value={model}
            style={{ width: 160 }}
            onChange={(v) => setModel(v)}
            options={[
              { value: "last_touch", label: "last_touch" },
              { value: "first_touch", label: "first_touch" },
            ]}
          />
        </span>
        <Button type="primary" loading={loading} onClick={run}>
          Attribute
        </Button>
      </Space>

      {error && (
        <Alert
          style={{ marginTop: 16 }}
          type="error"
          showIcon
          message={error}
        />
      )}

      {result && (
        <>
          <Divider />
          <Space size="large">
            <Statistic title="Model" value={result.model} />
            <Statistic
              title="Total conversions"
              value={result.total_conversions}
            />
            <Statistic title="Unattributed" value={result.unattributed} />
          </Space>
          <Table
            style={{ marginTop: 16 }}
            size="small"
            pagination={false}
            dataSource={rows}
            columns={[
              { title: "Campaign", dataIndex: "campaign", key: "campaign" },
              { title: "Sent", dataIndex: "sent", key: "sent" },
              {
                title: "Conversions",
                dataIndex: "conversions",
                key: "conversions",
              },
              { title: "Rate", dataIndex: "rate", key: "rate" },
            ]}
          />
        </>
      )}
    </Card>
  );
}

// ---- Reports panel -----------------------------------------------------------

function ReportsPanel() {
  const [name, setName] = useState<ReportName>("active_users");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.report(name);
      setResult(res as Record<string, unknown>);
    } catch (e) {
      setError(errMsg(e));
      message.error("Report failed");
    } finally {
      setLoading(false);
    }
  }

  // Render scalar fields as Statistics; arrays/objects as a small key/value list.
  function renderResult(r: Record<string, unknown>) {
    const scalars = Object.entries(r).filter(
      ([, v]) => typeof v === "number" || typeof v === "string",
    );
    const complex = Object.entries(r).filter(
      ([, v]) => typeof v !== "number" && typeof v !== "string",
    );
    return (
      <>
        <Space size="large" wrap>
          {scalars.map(([k, v]) => (
            <Statistic key={k} title={k} value={v as number | string} />
          ))}
        </Space>
        {complex.length > 0 && (
          <Table
            style={{ marginTop: 16 }}
            size="small"
            pagination={false}
            dataSource={complex.map(([k, v]) => ({
              key: k,
              field: k,
              value: JSON.stringify(v),
            }))}
            columns={[
              { title: "Field", dataIndex: "field", key: "field" },
              { title: "Value", dataIndex: "value", key: "value" },
            ]}
          />
        )}
      </>
    );
  }

  return (
    <Card>
      <Title level={4}>Reports</Title>
      <Paragraph type="secondary">
        The operator reports opened day-to-day (M9).
      </Paragraph>

      <Space>
        <Select<ReportName>
          aria-label="report-name"
          value={name}
          style={{ width: 220 }}
          onChange={(v) => setName(v)}
          options={REPORT_NAMES.map((n) => ({ value: n, label: n }))}
        />
        <Button type="primary" loading={loading} onClick={run}>
          Run report
        </Button>
      </Space>

      {error && (
        <Alert
          style={{ marginTop: 16 }}
          type="error"
          showIcon
          message={error}
        />
      )}

      {result && (
        <>
          <Divider />
          {renderResult(result)}
        </>
      )}
    </Card>
  );
}

// ---- Auto-insights panel -----------------------------------------------------

function InsightsPanel() {
  const [seriesText, setSeriesText] = useState("10, 11, 9, 10, 42, 8, 10");
  const [zThreshold, setZThreshold] = useState<number | null>(2);
  const [insights, setInsights] = useState<Insight[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const series = seriesText
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean)
      .map(Number);
    if (series.length === 0 || series.some((n) => Number.isNaN(n))) {
      setError("Enter a comma-separated list of numbers.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsApi.insights({
        series,
        z_threshold: zThreshold ?? undefined,
      });
      setInsights(((res as { insights?: Insight[] }).insights ?? []) as Insight[]);
    } catch (e) {
      setError(errMsg(e));
      message.error("Insights failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <Title level={4}>Auto-insights</Title>
      <Paragraph type="secondary">
        Flags spikes and drops in a numeric series (z-score based).
      </Paragraph>

      <Space wrap>
        <Input
          aria-label="insights-series"
          style={{ width: 320 }}
          value={seriesText}
          placeholder="10, 11, 9, 42, 8"
          onChange={(e) => setSeriesText(e.target.value)}
        />
        <span>
          <Text>z_threshold: </Text>
          <InputNumber
            aria-label="z-threshold"
            min={0}
            step={0.5}
            value={zThreshold}
            onChange={(v) => setZThreshold(v ?? null)}
          />
        </span>
        <Button type="primary" loading={loading} onClick={run}>
          Detect
        </Button>
      </Space>

      {error && (
        <Alert
          style={{ marginTop: 16 }}
          type="error"
          showIcon
          message={error}
        />
      )}

      {insights && (
        <>
          <Divider />
          {insights.length === 0 ? (
            <Empty description="No notable spikes or drops" />
          ) : (
            <List
              dataSource={insights}
              renderItem={(it) => (
                <List.Item>
                  <Space>
                    <Tag color={it.direction === "up" ? "green" : "red"}>
                      {it.direction}
                    </Tag>
                    <Text>{it.narrative}</Text>
                  </Space>
                </List.Item>
              )}
            />
          )}
        </>
      )}
    </Card>
  );
}

// ---- Page --------------------------------------------------------------------

export default function AnalyticsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <Title level={3}>{t("nav.analytics") || "Analytics (M4+M9)"}</Title>
      <Tabs
        defaultActiveKey="funnel"
        items={[
          { key: "funnel", label: "Funnel", children: <FunnelPanel /> },
          {
            key: "attribution",
            label: "Attribution",
            children: <AttributionPanel />,
          },
          { key: "reports", label: "Reports", children: <ReportsPanel /> },
          { key: "insights", label: "Auto-insights", children: <InsightsPanel /> },
        ]}
      />
    </div>
  );
}
