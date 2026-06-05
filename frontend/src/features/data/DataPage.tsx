// Data Platform (M8) screen — ops-facing / internal.
// Three tools over the data-platform service:
//   * DQC dashboard (loads on mount): metric checks pass/fail + alerts list
//   * Identity resolve: identifiers -> canonical id
//   * Suppression check: customer_ids -> kept vs suppressed
//   * Ingest tester (optional): events JSON -> clean/quarantined/deduped counts
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Input,
  List,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { dataApi } from "../../api/client";

const { TextArea } = Input;
const { Text, Title } = Typography;

// ---- backend shapes (service returns `any`; see services/data_platform.py) ----

interface DqcAlert {
  check: string;
  value: number;
  threshold: number;
}
interface DqcReport {
  ok: boolean;
  metrics: Record<string, number | null>;
  alerts: DqcAlert[];
}
interface ResolveResult {
  canonical_id: string | null;
  resolved: boolean;
}
interface SuppressionResult {
  allowed: string[];
  suppressed: string[];
}
interface IngestResult {
  clean: number;
  quarantined: number;
  deduped: number;
  quarantine_reasons: (string | null)[];
}

// Metrics that have a threshold-backed pass/fail check. Others are informational.
const CHECKED_METRICS: Record<string, string> = {
  null_rate: "null_rate",
  dup_rate: "dup_rate",
  latency_hours: "freshness",
};

interface CheckRow {
  key: string;
  metric: string;
  value: number | null;
  alert?: DqcAlert;
  checked: boolean;
}

function buildCheckRows(report: DqcReport): CheckRow[] {
  const alertByCheck = new Map(report.alerts.map((a) => [a.check, a]));
  return Object.entries(report.metrics).map(([metric, value]) => {
    const checkName = CHECKED_METRICS[metric];
    const checked = checkName !== undefined;
    return {
      key: metric,
      metric,
      value,
      checked,
      alert: checkName ? alertByCheck.get(checkName) : undefined,
    };
  });
}

function fmtValue(v: number | null): string {
  if (v === null || v === undefined) return "—";
  return Number.isInteger(v) ? String(v) : v.toFixed(4);
}

export default function DataPage() {
  const { t } = useTranslation();

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Title level={3} style={{ margin: 0 }}>
        Data Platform (M8) · {t("nav.data")}
      </Title>
      <DqcDashboard />
      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <IdentityResolve />
        </Col>
        <Col xs={24} lg={12}>
          <SuppressionCheck />
        </Col>
      </Row>
      <IngestTester />
    </Space>
  );
}

// ---- DQC dashboard ----------------------------------------------------------

function DqcDashboard() {
  const [report, setReport] = useState<DqcReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = (await dataApi.dqc()) as DqcReport;
      setReport(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load DQC report.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const columns: ColumnsType<CheckRow> = [
    { title: "Check", dataIndex: "metric" },
    {
      title: "Value",
      dataIndex: "value",
      render: (v: number | null) => fmtValue(v),
    },
    {
      title: "Threshold",
      key: "threshold",
      render: (_: unknown, row: CheckRow) =>
        row.alert ? fmtValue(row.alert.threshold) : "—",
    },
    {
      title: "Status",
      key: "status",
      render: (_: unknown, row: CheckRow) => {
        if (!row.checked) return <Tag>info</Tag>;
        return row.alert ? (
          <Tag color="red">fail</Tag>
        ) : (
          <Tag color="green">pass</Tag>
        );
      },
    },
  ];

  return (
    <Card
      title="Data Quality Checks (DQC)"
      extra={
        <Button
          size="small"
          icon={<ReloadOutlined />}
          loading={loading}
          onClick={load}
        >
          Refresh
        </Button>
      }
    >
      {loading && !report ? (
        <div style={{ textAlign: "center", padding: 24 }}>
          <Spin />
        </div>
      ) : error ? (
        <Alert type="error" showIcon message={error} />
      ) : report ? (
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Space>
            <Text>Overall:</Text>
            {report.ok ? (
              <Tag color="green">all checks passing</Tag>
            ) : (
              <Tag color="red">{report.alerts.length} alert(s)</Tag>
            )}
          </Space>
          <Table<CheckRow>
            rowKey="key"
            size="small"
            pagination={false}
            dataSource={buildCheckRows(report)}
            columns={columns}
          />
          <div>
            <Text strong>Alerts</Text>
            {report.alerts.length === 0 ? (
              <div aria-label="dqc-alerts-empty">
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="No alerts"
                />
              </div>
            ) : (
              <List<DqcAlert>
                size="small"
                aria-label="dqc-alerts"
                dataSource={report.alerts}
                renderItem={(a) => (
                  <List.Item>
                    <Tag color="red">{a.check}</Tag>
                    value {fmtValue(a.value)} &gt; threshold{" "}
                    {fmtValue(a.threshold)}
                  </List.Item>
                )}
              />
            )}
          </div>
        </Space>
      ) : null}
    </Card>
  );
}

// ---- Identity resolve -------------------------------------------------------

function IdentityResolve() {
  const [customerId, setCustomerId] = useState("");
  const [phone, setPhone] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [result, setResult] = useState<ResolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function resolve() {
    const identifiers: Record<string, string> = {};
    if (customerId.trim()) identifiers.customer_id = customerId.trim();
    if (phone.trim()) identifiers.phone = phone.trim();
    if (deviceId.trim()) identifiers.device_id = deviceId.trim();
    if (Object.keys(identifiers).length === 0) {
      setError("Enter at least one identifier.");
      setResult(null);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = (await dataApi.resolve(identifiers)) as ResolveResult;
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resolve failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Identity Resolve" style={{ height: "100%" }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Input
          aria-label="resolve-customer-id"
          placeholder="customer_id"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
        />
        <Input
          aria-label="resolve-phone"
          placeholder="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <Input
          aria-label="resolve-device-id"
          placeholder="device_id"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
        />
        <Button type="primary" loading={loading} onClick={resolve}>
          Resolve
        </Button>
        {error && <Alert type="error" showIcon message={error} />}
        {result && (
          <div aria-label="resolve-result">
            {result.resolved && result.canonical_id ? (
              <Statistic title="Canonical ID" value={result.canonical_id} />
            ) : (
              <Alert
                type="warning"
                showIcon
                message="No canonical id resolved for those identifiers."
              />
            )}
          </div>
        )}
      </Space>
    </Card>
  );
}

// ---- Suppression check ------------------------------------------------------

function SuppressionCheck() {
  const [raw, setRaw] = useState("");
  const [result, setResult] = useState<SuppressionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function check() {
    const ids = raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (ids.length === 0) {
      setError("Enter one or more comma-separated customer_ids.");
      setResult(null);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = (await dataApi.suppressionCheck(ids)) as SuppressionResult;
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Suppression check failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Suppression Check" style={{ height: "100%" }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <TextArea
          aria-label="suppression-ids"
          rows={3}
          placeholder="customer ids, comma separated (e.g. w1, w2, w5)"
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
        />
        <Button type="primary" loading={loading} onClick={check}>
          Check
        </Button>
        {error && <Alert type="error" showIcon message={error} />}
        {result && (
          <Descriptions
            aria-label="suppression-result"
            bordered
            column={1}
            size="small"
          >
            <Descriptions.Item label="Kept (allowed)">
              <Space wrap>
                {result.allowed.length === 0 ? (
                  <Text type="secondary">none</Text>
                ) : (
                  result.allowed.map((id) => (
                    <Tag color="green" key={id}>
                      {id}
                    </Tag>
                  ))
                )}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="Suppressed">
              <Space wrap>
                {result.suppressed.length === 0 ? (
                  <Text type="secondary">none</Text>
                ) : (
                  result.suppressed.map((id) => (
                    <Tag color="red" key={id}>
                      {id}
                    </Tag>
                  ))
                )}
              </Space>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Space>
    </Card>
  );
}

// ---- Ingest tester (optional) ----------------------------------------------

const INGEST_PLACEHOLDER = `[
  {"event_name": "Transfer", "customer_id": "w1", "amount": 100, "ts_utc": "2026-01-01T10:00:00"}
]`;

function IngestTester() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    let events: unknown;
    try {
      events = JSON.parse(text || "[]");
    } catch {
      setError("Events must be valid JSON.");
      setResult(null);
      return;
    }
    if (!Array.isArray(events)) {
      setError("Events JSON must be an array.");
      setResult(null);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = (await dataApi.ingest(events)) as IngestResult;
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ingest failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Ingest Tester">
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <TextArea
          aria-label="ingest-events"
          rows={6}
          placeholder={INGEST_PLACEHOLDER}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <Button type="primary" loading={loading} onClick={run}>
          Ingest
        </Button>
        {error && <Alert type="error" showIcon message={error} />}
        {result && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <Space size="large" wrap>
              <Statistic title="Clean" value={result.clean} />
              <Statistic title="Quarantined" value={result.quarantined} />
              <Statistic title="Deduped" value={result.deduped} />
            </Space>
            {result.quarantine_reasons.length > 0 && (
              <div>
                <Text strong>Quarantine reasons</Text>
                <List
                  size="small"
                  aria-label="quarantine-reasons"
                  dataSource={result.quarantine_reasons}
                  renderItem={(r) => (
                    <List.Item>
                      <Tag color="orange">{r ?? "unknown"}</Tag>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </Space>
        )}
      </Space>
    </Card>
  );
}
