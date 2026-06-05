// Content (M6 AI Copywriting) screen.
//
// - Generate panel: goal + product + locales + n + channel + tone ->
//   contentApi.generate -> variants grouped by locale, each with inline
//   compliance tags (meta.violations / a green "compliant" tag). Arabic text is
//   rendered RTL (dir="rtl") so it reads correctly.
// - Compliance checker: text + channel + product -> contentApi.compliance ->
//   ok/violations + fixed_text (highlighted when it differs from the input).
// - Select-best (optional): a small records JSON -> contentApi.selectBest ->
//   the winning variant id.
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";

import { contentApi } from "../../api/client";

const { Title, Text, Paragraph } = Typography;

// --- shared option lists ------------------------------------------------------
const LOCALES = [
  { value: "en", label: "English (en)" },
  { value: "ar", label: "العربية (ar)" },
  { value: "hi", label: "हिन्दी (hi)" },
  { value: "tl", label: "Tagalog (tl)" },
];
const PRODUCTS = ["Wallet", "Loan", "Remittance"];
const CHANNELS = ["push", "sms", "in_app"];
const TONES = ["friendly", "urgent", "formal"];

// Arabic is the only RTL locale among Botim's markets.
const RTL_LOCALES = new Set(["ar"]);
const isRtlLocale = (loc: string) => RTL_LOCALES.has(loc);

// --- API response shapes (backend returns `any`; narrow locally) --------------
interface VariantMeta {
  seed?: number;
  goal?: string;
  product?: string;
  tone?: string;
  channel?: string;
  compliant?: boolean;
  violations?: string[];
  raw_text?: string;
  [k: string]: unknown;
}
interface Variant {
  locale: string;
  text: string;
  meta?: VariantMeta;
}
interface GenerateResponse {
  variants?: Variant[];
}
interface ComplianceResponse {
  ok: boolean;
  violations: string[];
  fixed_text: string;
}

interface GenerateForm {
  goal: string;
  product: string;
  locales: string[];
  n: number;
  channel?: string;
  tone?: string;
}
interface ComplianceForm {
  text: string;
  channel?: string;
  product?: string;
}

// Human-readable label for a violation code (e.g. "banned_claim:guaranteed").
function violationTag(code: string) {
  return (
    <Tag color="error" key={code}>
      {code}
    </Tag>
  );
}

export default function ContentPage() {
  const { t } = useTranslation();

  // --- Generate panel -------------------------------------------------------
  const [genForm] = Form.useForm<GenerateForm>();
  const [variants, setVariants] = useState<Variant[] | null>(null);
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const handleGenerate = useCallback(async (values: GenerateForm) => {
    setGenLoading(true);
    setGenError(null);
    try {
      const res = (await contentApi.generate({
        goal: values.goal,
        product: values.product,
        locales: values.locales,
        n: values.n,
        channel: values.channel,
        tone: values.tone,
      })) as GenerateResponse;
      setVariants(res.variants ?? []);
    } catch (e) {
      setGenError((e as Error).message);
      setVariants(null);
    } finally {
      setGenLoading(false);
    }
  }, []);

  // Group generated variants by locale for rendering.
  const grouped = useMemo(() => {
    const map = new Map<string, Variant[]>();
    for (const v of variants ?? []) {
      const arr = map.get(v.locale) ?? [];
      arr.push(v);
      map.set(v.locale, arr);
    }
    return [...map.entries()];
  }, [variants]);

  // --- Compliance checker ---------------------------------------------------
  const [compForm] = Form.useForm<ComplianceForm>();
  const [compResult, setCompResult] = useState<ComplianceResponse | null>(null);
  const [compInput, setCompInput] = useState<string>("");
  const [compLoading, setCompLoading] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  const handleCompliance = useCallback(async (values: ComplianceForm) => {
    setCompLoading(true);
    setCompError(null);
    try {
      const res = (await contentApi.compliance({
        text: values.text,
        channel: values.channel,
        product: values.product,
      })) as ComplianceResponse;
      setCompInput(values.text);
      setCompResult(res);
    } catch (e) {
      setCompError((e as Error).message);
      setCompResult(null);
    } finally {
      setCompLoading(false);
    }
  }, []);

  // --- Select-best (optional) ----------------------------------------------
  const [recordsText, setRecordsText] = useState<string>(
    JSON.stringify(
      [
        { content_id: "copy_A", variant: "A", converted: true },
        { content_id: "copy_B", variant: "B", converted: false },
      ],
      null,
      2,
    ),
  );
  const [best, setBest] = useState<unknown>(null);
  const [bestLoading, setBestLoading] = useState(false);
  const [bestError, setBestError] = useState<string | null>(null);

  const handleSelectBest = useCallback(async () => {
    setBestLoading(true);
    setBestError(null);
    try {
      let records: unknown[];
      try {
        records = JSON.parse(recordsText);
      } catch {
        throw new Error("Records must be valid JSON (an array of objects).");
      }
      if (!Array.isArray(records)) {
        throw new Error("Records must be a JSON array.");
      }
      const res = (await contentApi.selectBest(records)) as { best?: unknown };
      setBest(res?.best ?? res);
    } catch (e) {
      setBestError((e as Error).message);
      setBest(null);
    } finally {
      setBestLoading(false);
    }
  }, [recordsText]);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Title level={3}>{t("nav.content")} (M6)</Title>

      <Row gutter={16}>
        {/* ---- Generate panel ---- */}
        <Col xs={24} lg={14}>
          <Card title="Generate copy" size="small" style={{ marginBottom: 16 }}>
            <Form
              form={genForm}
              layout="vertical"
              onFinish={handleGenerate}
              initialValues={{
                goal: "activate_wallet",
                product: "Wallet",
                locales: ["en", "ar"],
                n: 2,
                channel: "push",
                tone: "friendly",
              }}
            >
              <Row gutter={12}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="goal"
                    label="Goal"
                    rules={[{ required: true, message: "Goal is required" }]}
                  >
                    <Input aria-label="goal" placeholder="e.g. activate_wallet" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="product"
                    label="Product"
                    rules={[{ required: true, message: "Product is required" }]}
                  >
                    <Select
                      aria-label="product"
                      options={PRODUCTS.map((p) => ({ value: p, label: p }))}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="locales"
                label="Locales"
                rules={[{ required: true, message: "Pick at least one locale" }]}
              >
                <Select
                  aria-label="locales"
                  mode="multiple"
                  options={LOCALES}
                  placeholder="Select locales"
                />
              </Form.Item>

              <Row gutter={12}>
                <Col xs={24} sm={8}>
                  <Form.Item name="n" label="Variants (n)">
                    <InputNumber aria-label="n" min={1} max={10} style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item name="channel" label="Channel">
                    <Select
                      aria-label="channel"
                      allowClear
                      options={CHANNELS.map((c) => ({ value: c, label: c }))}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item name="tone" label="Tone">
                    <Select
                      aria-label="tone"
                      options={TONES.map((c) => ({ value: c, label: c }))}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Button type="primary" htmlType="submit" loading={genLoading}>
                Generate
              </Button>
            </Form>

            <Divider />

            {genError && (
              <Alert
                type="error"
                showIcon
                message="Generation failed"
                description={genError}
                style={{ marginBottom: 12 }}
              />
            )}

            {genLoading ? (
              <Spin />
            ) : variants === null ? (
              <Empty description="No variants yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : variants.length === 0 ? (
              <Empty description="No variants returned" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <div data-testid="variants">
                {grouped.map(([locale, items]) => (
                  <div key={locale} style={{ marginBottom: 16 }}>
                    <Text strong>{locale.toUpperCase()}</Text>
                    <Space direction="vertical" style={{ width: "100%", marginTop: 8 }}>
                      {items.map((v, i) => {
                        const violations = v.meta?.violations ?? [];
                        const compliant = v.meta?.compliant ?? violations.length === 0;
                        const rtl = isRtlLocale(v.locale);
                        return (
                          <Card
                            key={`${locale}-${i}`}
                            size="small"
                            data-testid={`variant-${locale}-${i}`}
                          >
                            <Paragraph
                              dir={rtl ? "rtl" : "ltr"}
                              style={{
                                textAlign: rtl ? "right" : "left",
                                marginBottom: 8,
                              }}
                            >
                              {v.text}
                            </Paragraph>
                            <Space wrap>
                              {compliant && violations.length === 0 ? (
                                <Tag color="success">compliant</Tag>
                              ) : (
                                <>
                                  {!compliant && <Tag color="warning">non-compliant</Tag>}
                                  {violations.map(violationTag)}
                                </>
                              )}
                            </Space>
                          </Card>
                        );
                      })}
                    </Space>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </Col>

        {/* ---- Compliance checker + Select-best ---- */}
        <Col xs={24} lg={10}>
          <Card title="Compliance checker" size="small" style={{ marginBottom: 16 }}>
            <Form form={compForm} layout="vertical" onFinish={handleCompliance}>
              <Form.Item
                name="text"
                label="Text"
                rules={[{ required: true, message: "Text is required" }]}
              >
                <Input.TextArea aria-label="compliance-text" rows={3} placeholder="Paste copy to check" />
              </Form.Item>
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item name="channel" label="Channel">
                    <Select
                      aria-label="compliance-channel"
                      allowClear
                      options={CHANNELS.map((c) => ({ value: c, label: c }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="product" label="Product">
                    <Select
                      aria-label="compliance-product"
                      allowClear
                      options={PRODUCTS.map((p) => ({ value: p, label: p }))}
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Button type="primary" htmlType="submit" loading={compLoading}>
                Check compliance
              </Button>
            </Form>

            {compError && (
              <Alert
                type="error"
                showIcon
                message="Compliance check failed"
                description={compError}
                style={{ marginTop: 12 }}
              />
            )}

            {compLoading ? (
              <Spin style={{ marginTop: 12 }} />
            ) : compResult ? (
              <div data-testid="compliance-result" style={{ marginTop: 12 }}>
                <Space wrap style={{ marginBottom: 8 }}>
                  {compResult.ok ? (
                    <Tag color="success">ok</Tag>
                  ) : (
                    <Tag color="error">not ok</Tag>
                  )}
                  {(compResult.violations ?? []).length === 0 ? (
                    <Tag color="default">no violations</Tag>
                  ) : (
                    (compResult.violations ?? []).map(violationTag)
                  )}
                </Space>
                <div>
                  <Text type="secondary">Fixed text</Text>
                  {compResult.fixed_text !== compInput && (
                    <Tag color="processing" style={{ marginInlineStart: 8 }}>
                      changed
                    </Tag>
                  )}
                  <pre
                    data-testid="fixed-text"
                    style={{
                      margin: "6px 0 0",
                      whiteSpace: "pre-wrap",
                      background:
                        compResult.fixed_text !== compInput ? "#fffbe6" : "#f6f6f6",
                      padding: 12,
                      borderRadius: 4,
                    }}
                  >
                    {compResult.fixed_text}
                  </pre>
                </div>
              </div>
            ) : null}
          </Card>

          <Card title="Select best (by conversions)" size="small">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Input.TextArea
                aria-label="records-json"
                rows={6}
                value={recordsText}
                onChange={(e) => setRecordsText(e.target.value)}
              />
              <Button onClick={handleSelectBest} loading={bestLoading}>
                Select best
              </Button>
              {bestError && (
                <Alert type="error" showIcon message="Select-best failed" description={bestError} />
              )}
              {best !== null && (
                <Alert
                  type="success"
                  showIcon
                  message="Winning variant"
                  description={
                    <pre data-testid="best-result" style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                      {typeof best === "string" ? best : JSON.stringify(best, null, 2)}
                    </pre>
                  }
                />
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
}
