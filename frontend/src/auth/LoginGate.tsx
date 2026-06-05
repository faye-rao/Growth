import { useState } from "react";
import { Card, Form, Input, Select, Button, Typography } from "antd";

// Minimal auth gate (MVP): stores the MOE-APPKEY (used by the API client) + a role
// in localStorage. Production should replace this with a real login->token exchange
// against the gateway (see docs/Frontend-Plan.md backend prerequisites).
export const ROLES = ["admin", "operator", "analyst"] as const;
export type Role = (typeof ROLES)[number];

export function getRole(): Role {
  return ((typeof localStorage !== "undefined" && localStorage.getItem("MOE_ROLE")) as Role) || "operator";
}

function hasKey(): boolean {
  return typeof localStorage !== "undefined" && !!localStorage.getItem("MOE_APPKEY");
}

export default function LoginGate({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState(hasKey());

  if (authed) return <>{children}</>;

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "#f0f2f5" }}>
      <Card style={{ width: 360 }} title="Botim Growth Console">
        <Typography.Paragraph type="secondary">
          Sign in with your API key to continue.
        </Typography.Paragraph>
        <Form
          layout="vertical"
          initialValues={{ appkey: "demo-appkey", role: "operator" }}
          onFinish={(v) => {
            localStorage.setItem("MOE_APPKEY", v.appkey);
            localStorage.setItem("MOE_ROLE", v.role);
            setAuthed(true);
          }}
        >
          <Form.Item label="API key (MOE-APPKEY)" name="appkey" rules={[{ required: true }]}>
            <Input.Password placeholder="MOE-APPKEY" aria-label="appkey" />
          </Form.Item>
          <Form.Item label="Role" name="role">
            <Select options={ROLES.map((r) => ({ value: r, label: r }))} aria-label="role" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            Sign in
          </Button>
        </Form>
      </Card>
    </div>
  );
}
