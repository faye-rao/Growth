// Editable A/B/N variants table — add/remove rows, edit name/weight/content_id.
import { Button, InputNumber, Input, Space, Table } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { VariantRow } from "./wizardTypes";

interface Props {
  variants: VariantRow[];
  onChange: (variants: VariantRow[]) => void;
}

let seq = 0;
function nextKey(): string {
  seq += 1;
  return `var_${Date.now()}_${seq}`;
}

export default function VariantsTable({ variants, onChange }: Props) {
  function update(key: string, patch: Partial<VariantRow>) {
    onChange(variants.map((v) => (v.key === key ? { ...v, ...patch } : v)));
  }

  function addRow() {
    const next: VariantRow = {
      key: nextKey(),
      name: `V${variants.length + 1}`,
      weight: 1,
      content_id: "",
    };
    onChange([...variants, next]);
  }

  function removeRow(key: string) {
    onChange(variants.filter((v) => v.key !== key));
  }

  const columns: ColumnsType<VariantRow> = [
    {
      title: "Name",
      dataIndex: "name",
      render: (_, row) => (
        <Input
          aria-label={`variant-name-${row.key}`}
          value={row.name}
          onChange={(e) => update(row.key, { name: e.target.value })}
        />
      ),
    },
    {
      title: "Weight",
      dataIndex: "weight",
      width: 120,
      render: (_, row) => (
        <InputNumber
          aria-label={`variant-weight-${row.key}`}
          min={0}
          step={1}
          value={row.weight}
          onChange={(val) => update(row.key, { weight: Number(val) || 0 })}
        />
      ),
    },
    {
      title: "Content ID",
      dataIndex: "content_id",
      render: (_, row) => (
        <Input
          aria-label={`variant-content-${row.key}`}
          value={row.content_id}
          onChange={(e) => update(row.key, { content_id: e.target.value })}
        />
      ),
    },
    {
      title: "",
      dataIndex: "actions",
      width: 56,
      render: (_, row) => (
        <Button
          type="text"
          danger
          aria-label={`remove-variant-${row.key}`}
          icon={<DeleteOutlined />}
          onClick={() => removeRow(row.key)}
        />
      ),
    },
  ];

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      <Table<VariantRow>
        rowKey="key"
        size="small"
        pagination={false}
        dataSource={variants}
        columns={columns}
        locale={{ emptyText: "No variants — add at least one." }}
      />
      <Button icon={<PlusOutlined />} onClick={addRow}>
        Add variant
      </Button>
    </Space>
  );
}
