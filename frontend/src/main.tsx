import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import { useTranslation } from "react-i18next";
import App from "./App";
import ErrorBoundary from "./auth/ErrorBoundary";
import LoginGate from "./auth/LoginGate";
import i18n, { isRtl } from "./i18n";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

function Root() {
  const { i18n: i } = useTranslation();
  const dir = isRtl(i.language) ? "rtl" : "ltr";
  // keep <html dir> in sync for full RTL mirroring
  if (typeof document !== "undefined") document.documentElement.dir = dir;
  return (
    <ConfigProvider direction={dir as "ltr" | "rtl"}>
      <ErrorBoundary>
        <LoginGate>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </LoginGate>
      </ErrorBoundary>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Root />
    </QueryClientProvider>
  </React.StrictMode>
);

// ensure i18n is initialized
void i18n;
