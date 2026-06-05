// Experiment screen (M7 — Shadow validation / 验证).
// Two panels:
//  1) Shadow split — assign customer_ids into shadow vs. control arms.
//  2) Comparison report — non-inferiority A/B report (shadow vs. control)
//     rendering a colour-coded verdict + rates + significance + diff CI.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Input,
  InputNumber,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { experimentApi } from "../../api/client";

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

// --- shapes (backend returns `any`; we model the fields we render) -----------
interface ShadowReportResult {
  control_sent: number;
  control_conversions: number;
  control_rate: number;
  shadow_sent: number;
  shadow_conversions: number;
  shadow_rate: number;
  absolute_lift: number;
  relative_lift: number;
  z: number;
  p_value: number;
  significant: boolean;
  non_inferiority_margin: number;
  verdict: string;
  diff_ci_low: number;
  diff_ci_high: number;
}

type Verdict = "shadow_better" | "not_worse" | "worse" | "inconclusive";

const VERDICT_COLOR: Record<Verdict, string> = {
  shadow_better: "green",
  not_worse: "blue",
  worse: "red",
  inconclusive: "default",
};

const VERDICT_LABEL: Record<Verdict, string> = {
  shadow_better: "Shadow better",
  not_worse: "Not worse (passes gate)",
  worse: "Worse",
  inconclusive: "Inconclusive",
};

function verdictColor(v: string): string {
  return VERDICT_COLOR[v as Verdict] ?? "default";
}
function verdictLabel(v: string): string {
  return VERDICT_LABEL[v as Verdict] ?? v;
}

function pct(x: number): string {
  return `${(x * 100).toFixed(2)}%`;
}

// Prefilled sample where shadow ≈ control (near-identical rates).
const SAMPLE_CONTROL = JSON.stringify(
  [
    { customer_id: "c1", status: "sent", converted: true },
    { customer_id: "c2", status: "sent", converted: true },
    { customer_id: "c3", status: "sent", converted: false },
    { customer_id: "c4", status: "sent", converted: false },
    { customer_id: "c5", status: "sent", converted: true },
    { customer_id: "c6", status: "sent", converted: false },
    { customer_id: "c7", status: "sent", converted: false },
    { customer_id: "c8", status: "sent", converted: false },
    { customer_id: "c9", status: "sent", converted: true },
    { customer_id: "c10", status: "sent", converted: false },
  ],
  null,
  2,
);

const SAMPLE_SHADOW = JSON.stringify(
  [
    { customer_id: "s1", status: "sent", converted: true },
    { customer_id: "s2", status: "sent", converted: false },
    { customer_id: "s3", status: "sent", converted: true },
    { customer_id: "s4", status: "sent", converted: false },
    { customer_id: "s5", status: "sent", converted: false },
    { customer_id: "s6", status: "sent", converted: true },
    { customer_id: "s7", status: "sent", converted: false },
    { customer_id: "s8", status: "sent", converted: false },
    { customer_id: "s9", status: "sent", converted: false },
    { customer_id: "s10", status: "sent", converted: true },
  ],
  null,
  2,
);

// --- arm-count helpers --------------------------------------------------------
interface ArmCount {
  arm: string;
  count: number;
}

// The split endpoint may return either a per-customer assignment map
// ({id: "shadow"|"control"}) or arm->ids lists. Normalise to counts.
function toArmCounts(res: unknown): ArmCount[] {
  if (!res || typeof res !== "object") return [];
  const obj = res as Record<string, unknown>;

  // Common envelopes.
  const inner =
    (obj.assignments as unknown) ??
    (obj.arms as unknown) ??
    (obj.split as unknown) ??
    obj;

  const counts: Record<string, number> = {};

  if (inner && typeof inner === "object") {
    for (const [k, v] of Object.entries(inner as Record<string, unknown>)) {
      if (Array.isArray(v)) {
        // arm -> [ids]
        counts[k] = (counts[k] ?? 0) + v.length;
      } else if (typeof v === "number") {
        // arm -> count
        counts[k] = (counts[k] ?? 0) + v;
      } else if (typeof v === "string") {
        // customer_id -> arm
        counts[v] = (counts[v] ?? 0) + 1;
      }
    }
  }
  return Object.entries(counts)
    .map(([arm, count]) => ({ arm, count }))
    .sort((a, b) => a.arm.localeCompare(b.arm));
}

function parseRecords(text: string): { records: unknown[]; error: string | null } {
  try {
    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) {
      return { records: [], error: "Expected a JSON array of records." };
    }
    return { records: parsed, error: null };
  } catch (e) {
    return { records: [], error: e instanceof Error ? e.message : "Invalid JSON." };
  }
}

export default function ExperimentPage() {
  const { t } = useTranslation();
  const title = t("nav.experiment", "Experiment (M7)");

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        {title}
      </Typography.Title>
      <SplitPanel />
      <ReportPanel />
    </Space>
  );
}

// ----------------------------------------------------------------------------
function SplitPanel() {
  const [idsText, setIdsText] = useState("u1, u2, u3, u4, u5, u6, u7, u8, u9, u10");
  const [shadowPct, setShadowPct] = useState<number>(0.05);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [armCounts, setArmCounts] = useState<ArmCount[] | null>(null);

  const customerIds = useMemo(
    () =>
      idsText
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean),
    [idsText],
  );

  async function runSplit() {
    if (customerIds.length === 0) {
      setError("Enter at least one customer_id.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await experimentApi.split({
        customer_ids: customerIds,
        shadow_pct: shadowPct,
      });
      setArmCounts(toArmCounts(res));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Split failed.");
      setArmCounts(null);
    } finally {
      setLoading(false);
    }
  }

  const columns: ColumnsType<ArmCount> = [
    {
      title: "Arm",
      dataIndex: "arm",
      render: (arm: string) => (
        <Tag color={arm === "shadow" ? "purple" : "default"}>{arm}</Tag>
      ),
    },
    { title: "Count", dataIndex: "count" },
  ];

  const total = (armCounts ?? []).reduce((a, b) => a + b.count, 0);
  const shadowCount =
    (armCounts ?? []).find((a) => a.arm === "shadow")?.count ?? 0;
  const controlCount = total - shadowCount;

  return (
    <Card title="Shadow split">
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <div>
          <Text>Customer IDs (comma / whitespace separated)</Text>
          <TextArea
            aria-label="customer-ids"
            rows={3}
            value={idsText}
            onChange={(e) => setIdsText(e.target.value)}
          />
          <Text type="secondary">{customerIds.length} id(s) parsed</Text>
        </div>
        <Space>
          <Text>Shadow %</Text>
          <InputNumber
            aria-label="shadow-pct"
            min={0}
            max={1}
            step={0.05}
            value={shadowPct}
            onChange={(v) => setShadowPct(Number(v) || 0)}
          />
          <Text type="secondary">(0–1, default 0.05 = 5%)</Text>
          <Button type="primary" loading={loading} onClick={runSplit}>
            Split
          </Button>
        </Space>

        {error && <Alert type="error" showIcon message={error} />}

        {armCounts && (
          <>
            <Row gutter={16}>
              <Col>
                <Statistic title="Shadow arm" value={shadowCount} />
              </Col>
              <Col>
                <Statistic title="Control arm" value={controlCount} />
              </Col>
              <Col>
                <Statistic title="Total assigned" value={total} />
              </Col>
            </Row>
            <Table<ArmCount>
              rowKey="arm"
              size="small"
              columns={columns}
              dataSource={armCounts}
              pagination={false}
              locale={{ emptyText: "No assignments returned." }}
            />
          </>
        )}
      </Space>
    </Card>
  );
}

// ----------------------------------------------------------------------------
function ReportPanel() {
  const [controlText, setControlText] = useState(SAMPLE_CONTROL);
  const [shadowText, setShadowText] = useState(SAMPLE_SHADOW);
  const [margin, setMargin] = useState<number>(0.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ShadowReportResult | null>(null);

  async function runReport() {
    const c = parseRecords(controlText);
    const s = parseRecords(shadowText);
    if (c.error) {
      setError(`Control records: ${c.error}`);
      return;
    }
    if (s.error) {
      setError(`Shadow records: ${s.error}`);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = (await experimentApi.report({
        control_records: c.records,
        shadow_records: s.records,
        non_inferiority_margin: margin,
      })) as ShadowReportResult;
      setReport(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report failed.");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Comparison report (non-inferiority)">
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Each record needs <Text code>status</Text> ("sent") and{" "}
          <Text code>converted</Text> (true/false). Verdict is a non-inferiority
          decision on (shadow_rate − control_rate).
        </Paragraph>
        <Row gutter={16}>
          <Col span={12}>
            <Text>Control records (JSON)</Text>
            <TextArea
              aria-label="control-records"
              rows={10}
              value={controlText}
              onChange={(e) => setControlText(e.target.value)}
            />
          </Col>
          <Col span={12}>
            <Text>Shadow records (JSON)</Text>
            <TextArea
              aria-label="shadow-records"
              rows={10}
              value={shadowText}
              onChange={(e) => setShadowText(e.target.value)}
            />
          </Col>
        </Row>
        <Space>
          <Text>Non-inferiority margin</Text>
          <InputNumber
            aria-label="non-inferiority-margin"
            min={0}
            max={1}
            step={0.01}
            value={margin}
            onChange={(v) => setMargin(Number(v) || 0)}
          />
          <Button type="primary" loading={loading} onClick={runReport}>
            Compare
          </Button>
        </Space>

        {error && <Alert type="error" showIcon message={error} />}

        {report && (
          <>
            <Divider style={{ margin: "8px 0" }} />
            <Space align="center">
              <Text strong>Verdict:</Text>
              <Tag
                aria-label="verdict-tag"
                color={verdictColor(report.verdict)}
                style={{ fontSize: 14, padding: "2px 10px" }}
              >
                {verdictLabel(report.verdict)}
              </Tag>
            </Space>

            <Row gutter={16}>
              <Col>
                <Statistic
                  title="Control rate"
                  value={pct(report.control_rate)}
                />
              </Col>
              <Col>
                <Statistic
                  title="Shadow rate"
                  value={pct(report.shadow_rate)}
                />
              </Col>
              <Col>
                <Statistic
                  title="Absolute lift"
                  value={pct(report.absolute_lift)}
                  valueStyle={{
                    color: report.absolute_lift >= 0 ? "#3f8600" : "#cf1322",
                  }}
                />
              </Col>
              <Col>
                <Statistic
                  title="Relative lift"
                  value={pct(report.relative_lift)}
                  valueStyle={{
                    color: report.relative_lift >= 0 ? "#3f8600" : "#cf1322",
                  }}
                />
              </Col>
            </Row>

            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Control (conv / sent)">
                {report.control_conversions} / {report.control_sent}
              </Descriptions.Item>
              <Descriptions.Item label="Shadow (conv / sent)">
                {report.shadow_conversions} / {report.shadow_sent}
              </Descriptions.Item>
              <Descriptions.Item label="z">
                {report.z.toFixed(4)}
              </Descriptions.Item>
              <Descriptions.Item label="p-value">
                {report.p_value.toFixed(4)}{" "}
                <Tag color={report.significant ? "red" : "default"}>
                  {report.significant ? "significant" : "not significant"}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Diff 95% CI">
                [{report.diff_ci_low.toFixed(4)}, {report.diff_ci_high.toFixed(4)}]
              </Descriptions.Item>
              <Descriptions.Item label="Margin">
                {report.non_inferiority_margin}
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Space>
    </Card>
  );
}
