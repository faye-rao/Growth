// Campaign screen: a campaign list + a 3-step "New campaign" wizard
// (Target users -> Content A/B/N -> Schedule & goals -> Run).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Descriptions,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Statistic,
  Steps,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { campaignApi, audienceApi } from "../../api/client";
import VariantsTable from "./VariantsTable";
import FlowCanvas from "./FlowCanvas";
import {
  buildRunRequest,
  defaultWizardState,
  parseAudience,
  validateVariants,
  type TriggerType,
  type WizardState,
} from "./wizardTypes";

const { TextArea } = Input;
const { Text } = Typography;

// RunResult shape returned by the backend runner (see orchestration/runner.py).
interface RunResultSummary {
  campaign_id: string;
  audience_size: number;
  eligible_size: number;
  sent_by_variant?: Record<string, number>;
  sent_count?: number;
  control_count: number;
  capped_count: number;
  not_sent_count: number;
  excluded_no_trigger?: number;
}

interface CampaignListItem {
  id: string;
  channel: string;
  variants: number;
  sent: number;
  status: string;
}

function sentTotal(r: RunResultSummary): number {
  if (typeof r.sent_count === "number") return r.sent_count;
  return Object.values(r.sent_by_variant ?? {}).reduce((a, b) => a + b, 0);
}

export default function CampaignPage() {
  const { t } = useTranslation();

  return (
    <Card title={t("campaign.title")}>
      <Tabs
        defaultActiveKey="campaigns"
        items={[
          { key: "campaigns", label: "Campaigns", children: <CampaignsTab /> },
          { key: "flow", label: "Flow", children: <FlowCanvas /> },
        ]}
      />
    </Card>
  );
}

// The original campaign list + "New campaign" wizard, now the first tab.
function CampaignsTab() {
  const { t } = useTranslation();
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [wizardOpen, setWizardOpen] = useState(false);

  const listColumns: ColumnsType<CampaignListItem> = [
    { title: "Campaign ID", dataIndex: "id" },
    { title: "Channel", dataIndex: "channel" },
    { title: "Variants", dataIndex: "variants" },
    { title: "Sent", dataIndex: "sent" },
    {
      title: "Status",
      dataIndex: "status",
      render: (s: string) => <Tag color="green">{s}</Tag>,
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16, justifyContent: "flex-end", width: "100%" }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setWizardOpen(true)}
        >
          {t("campaign.new")}
        </Button>
      </Space>
      <Table<CampaignListItem>
        rowKey="id"
        dataSource={campaigns}
        columns={listColumns}
        pagination={false}
        locale={{ emptyText: "No campaigns yet — create one." }}
      />
      {wizardOpen && (
        <CampaignWizard
          onClose={() => setWizardOpen(false)}
          onLaunched={(item) => setCampaigns((prev) => [item, ...prev])}
        />
      )}
    </>
  );
}

interface WizardProps {
  onClose: () => void;
  onLaunched: (item: CampaignListItem) => void;
}

function CampaignWizard({ onClose, onLaunched }: WizardProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  const [state, setState] = useState<WizardState>(defaultWizardState());
  const [sizeLoading, setSizeLoading] = useState(false);
  const [audienceError, setAudienceError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResultSummary | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  function patch(p: Partial<WizardState>) {
    setState((s) => ({ ...s, ...p }));
  }

  async function estimateSize() {
    const { spec, error } = parseAudience(state.audienceJson);
    if (error || !spec) {
      setAudienceError(error ?? "Invalid audience spec.");
      return;
    }
    setAudienceError(null);
    setSizeLoading(true);
    try {
      const res = await audienceApi.size(spec);
      patch({ estimatedSize: res.size });
    } catch (e) {
      setAudienceError(e instanceof Error ? e.message : "Failed to estimate size.");
    } finally {
      setSizeLoading(false);
    }
  }

  function next() {
    if (step === 0) {
      const { error } = parseAudience(state.audienceJson);
      if (error) {
        setAudienceError(error);
        return;
      }
      setAudienceError(null);
    }
    if (step === 1) {
      const v = validateVariants(state.variants);
      if (!v.ok) {
        message.error(v.message);
        return;
      }
    }
    setStep((s) => Math.min(s + 1, 2));
  }

  function prev() {
    setStep((s) => Math.max(s - 1, 0));
  }

  async function run() {
    const v = validateVariants(state.variants);
    if (!v.ok) {
      message.error(v.message);
      setRunError(v.message ?? "Invalid variants.");
      return;
    }
    const { error } = parseAudience(state.audienceJson);
    if (error) {
      message.error(error);
      setRunError(error);
      return;
    }
    setRunError(null);
    setRunning(true);
    try {
      const req = buildRunRequest(state);
      const res = (await campaignApi.run(req)) as RunResultSummary;
      setResult(res);
      onLaunched({
        id: req.id,
        channel: req.channel,
        variants: req.variants.length,
        sent: sentTotal(res),
        status: "completed",
      });
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Campaign run failed.");
    } finally {
      setRunning(false);
    }
  }

  const steps = [
    { title: t("campaign.step_audience") },
    { title: t("campaign.step_content") },
    { title: t("campaign.step_schedule") },
  ];

  return (
    <Modal
      open
      title={t("campaign.new")}
      width={720}
      onCancel={onClose}
      footer={null}
    >
      <Steps current={step} items={steps} style={{ marginBottom: 24 }} />

      <div style={{ minHeight: 280 }}>
        {step === 0 && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <Text>Audience (SegmentSpec JSON)</Text>
            <TextArea
              aria-label="audience-spec"
              rows={10}
              value={state.audienceJson}
              onChange={(e) => patch({ audienceJson: e.target.value })}
            />
            <Space>
              <Button onClick={estimateSize} loading={sizeLoading}>
                Estimate size
              </Button>
              {state.estimatedSize !== null && (
                <Statistic
                  title="Estimated audience"
                  value={state.estimatedSize}
                  valueStyle={{ fontSize: 18 }}
                />
              )}
            </Space>
            {audienceError && (
              <Alert type="error" showIcon message={audienceError} />
            )}
          </Space>
        )}

        {step === 1 && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <VariantsTable
              variants={state.variants}
              onChange={(variants) => patch({ variants })}
            />
            <Space>
              <Text>Control %</Text>
              <InputNumber
                aria-label="control-pct"
                min={0}
                max={0.99}
                step={0.05}
                value={state.controlPct}
                onChange={(val) => patch({ controlPct: Number(val) || 0 })}
              />
              <Text type="secondary">(0–1, held out as control)</Text>
            </Space>
          </Space>
        )}

        {step === 2 && (
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            {!result && (
              <>
                <Space wrap>
                  <span>
                    <Text>Channel </Text>
                    <Select
                      aria-label="channel"
                      style={{ width: 140 }}
                      value={state.channel}
                      onChange={(channel) => patch({ channel })}
                      options={[
                        { value: "push", label: "push" },
                        { value: "sms", label: "sms" },
                        { value: "in_app", label: "in_app" },
                      ]}
                    />
                  </span>
                  <span>
                    <Text>Trigger </Text>
                    <Select<TriggerType>
                      aria-label="trigger-type"
                      style={{ width: 140 }}
                      value={state.triggerType}
                      onChange={(triggerType) => patch({ triggerType })}
                      options={[
                        { value: "batch", label: "batch" },
                        { value: "triggered", label: "triggered" },
                      ]}
                    />
                  </span>
                </Space>
                {state.triggerType === "triggered" && (
                  <span>
                    <Text>Trigger event </Text>
                    <Input
                      aria-label="trigger-event"
                      style={{ width: 220 }}
                      value={state.triggerEvent}
                      onChange={(e) => patch({ triggerEvent: e.target.value })}
                    />
                  </span>
                )}
                <Space wrap>
                  <span>
                    <Text>Start </Text>
                    <DatePicker
                      aria-label="start-date"
                      showTime
                      onChange={(d) => patch({ start: d ? d.toISOString() : null })}
                    />
                  </span>
                  <span>
                    <Text>End </Text>
                    <DatePicker
                      aria-label="end-date"
                      showTime
                      onChange={(d) => patch({ end: d ? d.toISOString() : null })}
                    />
                  </span>
                </Space>
                <Space>
                  <Text>Daily cap</Text>
                  <InputNumber
                    aria-label="daily-cap"
                    min={1}
                    value={state.dailyCap}
                    onChange={(val) => patch({ dailyCap: Number(val) || 1 })}
                  />
                </Space>
                {runError && <Alert type="error" showIcon message={runError} />}
              </>
            )}

            {result && (
              <Descriptions
                title="Run result"
                bordered
                column={2}
                size="small"
              >
                <Descriptions.Item label="Campaign">
                  {result.campaign_id}
                </Descriptions.Item>
                <Descriptions.Item label="Audience">
                  {result.audience_size}
                </Descriptions.Item>
                <Descriptions.Item label="Total sent">
                  {sentTotal(result)}
                </Descriptions.Item>
                <Descriptions.Item label="Control held out">
                  {result.control_count}
                </Descriptions.Item>
                <Descriptions.Item label="Frequency capped">
                  {result.capped_count}
                </Descriptions.Item>
                <Descriptions.Item label="Not sent (suppressed)">
                  {result.not_sent_count}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Space>
        )}
      </div>

      <Space style={{ marginTop: 24, justifyContent: "flex-end", width: "100%" }}>
        {result ? (
          <Button type="primary" onClick={onClose}>
            Done
          </Button>
        ) : (
          <>
            {step > 0 && <Button onClick={prev}>Prev</Button>}
            {step < 2 && (
              <Button type="primary" onClick={next}>
                Next
              </Button>
            )}
            {step === 2 && (
              <Button type="primary" loading={running} onClick={run}>
                {t("campaign.run")}
              </Button>
            )}
          </>
        )}
      </Space>
    </Modal>
  );
}
