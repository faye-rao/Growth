import { Layout, Menu, Select, Typography } from "antd";
import {
  TeamOutlined,
  SendOutlined,
  FunnelPlotOutlined,
  AppstoreOutlined,
  EditOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../store";

const { Header, Sider, Content } = Layout;

const NAV = [
  { key: "/audience", icon: <TeamOutlined />, tkey: "nav.audience" },
  { key: "/campaign", icon: <SendOutlined />, tkey: "nav.campaign" },
  { key: "/analytics", icon: <FunnelPlotOutlined />, tkey: "nav.analytics" },
  { key: "/personalization", icon: <AppstoreOutlined />, tkey: "nav.personalization" },
  { key: "/content", icon: <EditOutlined />, tkey: "nav.content" },
  { key: "/experiment", icon: <ExperimentOutlined />, tkey: "nav.experiment" },
  { key: "/data", icon: <DatabaseOutlined />, tkey: "nav.data" },
];

export default function AppLayout() {
  const { t, i18n } = useTranslation();
  const loc = useLocation();
  const setLocale = useAppStore((s) => s.setLocale);

  const onLang = (lng: string) => {
    i18n.changeLanguage(lng);
    setLocale(lng);
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsible>
        <div style={{ color: "#fff", padding: 16, fontWeight: 600 }}>{t("app")}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[NAV.find((n) => loc.pathname.startsWith(n.key))?.key || "/audience"]}
          items={NAV.map((n) => ({
            key: n.key,
            icon: n.icon,
            label: <Link to={n.key}>{t(n.tkey)}</Link>,
          }))}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between", paddingInline: 16 }}>
          <Typography.Text strong>{t("app")}</Typography.Text>
          <Select
            aria-label={t("common.language")}
            value={i18n.language}
            style={{ width: 140 }}
            onChange={onLang}
            options={[
              { value: "en", label: "English" },
              { value: "ar", label: "العربية (RTL)" },
            ]}
          />
        </Header>
        <Content style={{ margin: 16 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
