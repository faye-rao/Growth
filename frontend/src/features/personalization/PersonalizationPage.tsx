// Personalization (千人千面 / M5) screen.
// Three sections:
//  1. Experience list (in-memory, this session) + "New experience" form
//     (key, audience_spec JSON, variations with multilingual payload, control_pct)
//       -> personalizationApi.register -> add to list as draft.
//  2. Publish button per experience -> personalizationApi.publish -> published.
//  3. Fetch tester (customer_id, experience_keys multi-select, locale)
//       -> personalizationApi.fetch -> render returned payload JSON.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  Divider,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { personalizationApi } from "../../api/client";
import VariationsTable from "./VariationsTable";
import {
  LOCALES,
  defaultAudienceJson,
  defaultVariationRow,
  parseAudience,
  toVariationIn,
  validateVariations,
} from "./types";
import type { ExperienceItem, Locale, VariationRow } from "./types";

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

export default function PersonalizationPage() {
  const { t } = useTranslation();
  const title = t("nav.personalization", "Personalization") + " (M5)";

  const [experiences, setExperiences] = useState<ExperienceItem[]>([]);

  // ---- New experience form state -------------------------------------------
  const [key, setKey] = useState("");
  const [audienceJson, setAudienceJson] = useState(defaultAudienceJson());
  const [variations, setVariations] = useState<VariationRow[]>([
    defaultVariationRow("A"),
    defaultVariationRow("B"),
  ]);
  const [controlPct, setControlPct] = useState(0.1);
  const [registering, setRegistering] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // ---- Per-experience publish state ----------------------------------------
  const [publishingKey, setPublishingKey] = useState<string | null>(null);

  async function register() {
    setFormError(null);
    if (!key.trim()) {
      setFormError("Experience key is required.");
      return;
    }
    if (experiences.some((e) => e.key === key.trim())) {
      setFormError(`Experience "${key.trim()}" already registered this session.`);
      return;
    }
    const { spec, error } = parseAudience(audienceJson);
    if (error || !spec) {
      setFormError(error ?? "Invalid audience spec.");
      return;
    }
    const v = validateVariations(variations);
    if (!v.ok) {
      setFormError(v.message ?? "Invalid variations.");
      return;
    }

    setRegistering(true);
    try {
      await personalizationApi.register({
        key: key.trim(),
        audience_spec: spec,
        variations: toVariationIn(variations),
        control_pct: controlPct,
      });
      setExperiences((prev) => [
        {
          key: key.trim(),
          variations: variations.length,
          control_pct: controlPct,
          status: "draft",
        },
        ...prev,
      ]);
      message.success(`Registered "${key.trim()}".`);
      // reset the form for the next experience
      setKey("");
      setAudienceJson(defaultAudienceJson());
      setVariations([defaultVariationRow("A"), defaultVariationRow("B")]);
      setControlPct(0.1);
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Failed to register experience.");
    } finally {
      setRegistering(false);
    }
  }

  async function publish(expKey: string) {
    setPublishingKey(expKey);
    try {
      await personalizationApi.publish(expKey);
      setExperiences((prev) =>
        prev.map((e) => (e.key === expKey ? { ...e, status: "published" } : e)),
      );
      message.success(`Published "${expKey}".`);
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Failed to publish.");
    } finally {
      setPublishingKey(null);
    }
  }

  const listColumns: ColumnsType<ExperienceItem> = [
    { title: "Key", dataIndex: "key" },
    { title: "Variations", dataIndex: "variations", width: 110 },
    {
      title: "Control %",
      dataIndex: "control_pct",
      width: 110,
      render: (p: number) => `${Math.round(p * 100)}%`,
    },
    {
      title: "Status",
      dataIndex: "status",
      width: 120,
      render: (s: ExperienceItem["status"]) => (
        <Tag color={s === "published" ? "green" : "default"}>{s}</Tag>
      ),
    },
    {
      title: "",
      dataIndex: "actions",
      width: 130,
      render: (_, row) =>
        row.status === "draft" ? (
          <Button
            size="small"
            type="primary"
            aria-label={`publish-${row.key}`}
            loading={publishingKey === row.key}
            onClick={() => publish(row.key)}
          >
            Publish
          </Button>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
  ];

  return (
    <Card title={title}>
      <Space direction="vertical" style={{ width: "100%" }} size="large">
        {/* Section 1 — Experience list */}
        <section>
          <Divider orientation="left">Registered experiences</Divider>
          <Table<ExperienceItem>
            rowKey="key"
            dataSource={experiences}
            columns={listColumns}
            pagination={false}
            locale={{ emptyText: "No experiences yet — register one below." }}
          />
        </section>

        {/* Section 1b — New experience form */}
        <section>
          <Divider orientation="left">New experience</Divider>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <span>
              <Text>Key </Text>
              <Input
                aria-label="experience-key"
                style={{ width: 280 }}
                placeholder="e.g. home_banner"
                value={key}
                onChange={(e) => setKey(e.target.value)}
              />
            </span>

            <div>
              <Text>Audience spec (SegmentSpec JSON)</Text>
              <TextArea
                aria-label="audience-spec"
                rows={8}
                value={audienceJson}
                onChange={(e) => setAudienceJson(e.target.value)}
              />
            </div>

            <div>
              <Text strong>Variations</Text>
              <VariationsTable variations={variations} onChange={setVariations} />
            </div>

            <Space>
              <Text>Control %</Text>
              <InputNumber
                aria-label="control-pct"
                min={0}
                max={0.99}
                step={0.05}
                value={controlPct}
                onChange={(val) => setControlPct(Number(val) || 0)}
              />
              <Text type="secondary">(0–1, held out as control)</Text>
            </Space>

            {formError && <Alert type="error" showIcon message={formError} />}

            <Button
              type="primary"
              icon={<PlusOutlined />}
              loading={registering}
              onClick={register}
            >
              Register experience
            </Button>
          </Space>
        </section>

        {/* Section 3 — Fetch tester */}
        <section>
          <Divider orientation="left">Fetch tester</Divider>
          <FetchTester experienceKeys={experiences.map((e) => e.key)} />
        </section>
      </Space>
    </Card>
  );
}

// ---------------------------------------------------------------------------

interface FetchTesterProps {
  experienceKeys: string[];
}

function FetchTester({ experienceKeys }: FetchTesterProps) {
  const [customerId, setCustomerId] = useState("");
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [locale, setLocale] = useState<Locale>("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  async function runFetch() {
    setError(null);
    if (!customerId.trim()) {
      setError("customer_id is required.");
      return;
    }
    if (selectedKeys.length === 0) {
      setError("Select at least one experience key.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await personalizationApi.fetch({
        identifiers: { customer_id: customerId.trim() },
        experience_keys: selectedKeys,
        locale,
      });
      setResult(res.experiences ?? {});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fetch failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <Space wrap align="end">
        <span>
          <div>
            <Text>customer_id</Text>
          </div>
          <Input
            aria-label="customer-id"
            style={{ width: 220 }}
            placeholder="e.g. cust_123"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          />
        </span>
        <span>
          <div>
            <Text>Experience keys</Text>
          </div>
          <Select
            aria-label="experience-keys"
            mode="multiple"
            virtual={false}
            style={{ minWidth: 240 }}
            placeholder="Select registered experiences"
            value={selectedKeys}
            onChange={setSelectedKeys}
            options={experienceKeys.map((k) => ({ value: k, label: k }))}
          />
        </span>
        <span>
          <div>
            <Text>Locale</Text>
          </div>
          <Select<Locale>
            aria-label="locale"
            style={{ width: 100 }}
            value={locale}
            onChange={setLocale}
            options={LOCALES.map((l) => ({ value: l, label: l }))}
          />
        </span>
        <Button type="primary" loading={loading} onClick={runFetch}>
          Fetch
        </Button>
      </Space>

      {error && <Alert type="error" showIcon message={error} />}

      {result && (
        <div aria-label="fetch-result">
          {Object.keys(result).length === 0 ? (
            <Text type="secondary">No experiences returned.</Text>
          ) : (
            Object.entries(result).map(([k, payload]) => (
              <Card
                key={k}
                size="small"
                title={k}
                style={{ marginBottom: 8 }}
                aria-label={`result-${k}`}
              >
                {payload === null || payload === undefined ? (
                  <Text type="secondary" aria-label={`result-empty-${k}`}>
                    no content (control / miss / unpublished)
                  </Text>
                ) : (
                  <Paragraph>
                    <pre style={{ margin: 0 }} aria-label={`result-json-${k}`}>
                      {JSON.stringify(payload, null, 2)}
                    </pre>
                  </Paragraph>
                )}
              </Card>
            ))
          )}
        </div>
      )}
    </Space>
  );
}
