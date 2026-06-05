// Editable variations: each row has name + weight + a multilingual payload editor.
import { Button, Card, Input, InputNumber, Space, Typography } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import PayloadEditor from "./PayloadEditor";
import { defaultVariationRow } from "./types";
import type { LocalePayload, VariationRow } from "./types";

const { Text } = Typography;

interface Props {
  variations: VariationRow[];
  onChange: (variations: VariationRow[]) => void;
}

export default function VariationsTable({ variations, onChange }: Props) {
  function update(key: string, patch: Partial<VariationRow>) {
    onChange(variations.map((v) => (v.key === key ? { ...v, ...patch } : v)));
  }

  function setPayload(key: string, payload: LocalePayload) {
    update(key, { payload });
  }

  function addRow() {
    onChange([...variations, defaultVariationRow(`V${variations.length + 1}`)]);
  }

  function removeRow(key: string) {
    onChange(variations.filter((v) => v.key !== key));
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      {variations.length === 0 && (
        <Text type="secondary">No variations — add at least one.</Text>
      )}
      {variations.map((row) => (
        <Card
          key={row.key}
          size="small"
          title={
            <Space>
              <Text>Name</Text>
              <Input
                aria-label={`variation-name-${row.key}`}
                style={{ width: 160 }}
                value={row.name}
                onChange={(e) => update(row.key, { name: e.target.value })}
              />
              <Text>Weight</Text>
              <InputNumber
                aria-label={`variation-weight-${row.key}`}
                min={0}
                step={1}
                value={row.weight}
                onChange={(val) => update(row.key, { weight: Number(val) || 0 })}
              />
            </Space>
          }
          extra={
            <Button
              type="text"
              danger
              aria-label={`remove-variation-${row.key}`}
              icon={<DeleteOutlined />}
              onClick={() => removeRow(row.key)}
            />
          }
        >
          <Text type="secondary">Payload (per-locale key/value pairs)</Text>
          <PayloadEditor
            variationKey={row.key}
            value={row.payload}
            onChange={(payload) => setPayload(row.key, payload)}
          />
        </Card>
      ))}
      <Button icon={<PlusOutlined />} onClick={addRow}>
        Add variation
      </Button>
    </Space>
  );
}
