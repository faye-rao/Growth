// Multilingual payload editor: per-locale (en/ar/hi/tl) key/value pairs.
// Edits a single variation's LocalePayload; assembled into {en:{...},ar:{...}}.
import { Button, Input, Space, Table, Tabs, Typography } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { LOCALES, nextKey } from "./types";
import type { KVRow, Locale, LocalePayload } from "./types";

const { Text } = Typography;

interface Props {
  // identifies the owning variation (used to scope aria-labels in tests)
  variationKey: string;
  value: LocalePayload;
  onChange: (value: LocalePayload) => void;
}

export default function PayloadEditor({ variationKey, value, onChange }: Props) {
  function setLocale(locale: Locale, rows: KVRow[]) {
    onChange({ ...value, [locale]: rows });
  }

  function addRow(locale: Locale) {
    setLocale(locale, [...value[locale], { key: nextKey("kv"), k: "", v: "" }]);
  }

  function updateRow(locale: Locale, rowKey: string, patch: Partial<KVRow>) {
    setLocale(
      locale,
      value[locale].map((r) => (r.key === rowKey ? { ...r, ...patch } : r)),
    );
  }

  function removeRow(locale: Locale, rowKey: string) {
    setLocale(
      locale,
      value[locale].filter((r) => r.key !== rowKey),
    );
  }

  function columnsFor(locale: Locale): ColumnsType<KVRow> {
    return [
      {
        title: "Key",
        dataIndex: "k",
        render: (_, row) => (
          <Input
            aria-label={`payload-key-${variationKey}-${locale}-${row.key}`}
            placeholder="e.g. title"
            value={row.k}
            onChange={(e) => updateRow(locale, row.key, { k: e.target.value })}
          />
        ),
      },
      {
        title: "Value",
        dataIndex: "v",
        render: (_, row) => (
          <Input
            aria-label={`payload-val-${variationKey}-${locale}-${row.key}`}
            value={row.v}
            onChange={(e) => updateRow(locale, row.key, { v: e.target.value })}
          />
        ),
      },
      {
        title: "",
        dataIndex: "actions",
        width: 48,
        render: (_, row) => (
          <Button
            type="text"
            danger
            aria-label={`remove-kv-${variationKey}-${locale}-${row.key}`}
            icon={<DeleteOutlined />}
            onClick={() => removeRow(locale, row.key)}
          />
        ),
      },
    ];
  }

  const items = LOCALES.map((locale) => ({
    key: locale,
    label: locale.toUpperCase(),
    children: (
      <Space direction="vertical" style={{ width: "100%" }} size="small">
        <Table<KVRow>
          rowKey="key"
          size="small"
          pagination={false}
          dataSource={value[locale]}
          columns={columnsFor(locale)}
          locale={{ emptyText: <Text type="secondary">No {locale} pairs.</Text> }}
        />
        <Button
          size="small"
          icon={<PlusOutlined />}
          aria-label={`add-kv-${variationKey}-${locale}`}
          onClick={() => addRow(locale)}
        >
          Add {locale} pair
        </Button>
      </Space>
    ),
  }));

  return <Tabs size="small" items={items} />;
}
