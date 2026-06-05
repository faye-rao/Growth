import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import i18n from "../../i18n";

// jsdom lacks matchMedia; AntD's responsive observer needs it.
if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

// ECharts needs canvas + a sized container; stub it so charts render to nothing.
vi.mock("echarts-for-react", () => ({ default: () => null }));

// Keep tests offline — mock the API client (preserve the real ApiError export).
vi.mock("../../api/client", async () => {
  const actual = await vi.importActual<typeof import("../../api/client")>(
    "../../api/client",
  );
  return {
    ...actual,
    analyticsApi: {
      funnel: vi.fn(),
      attribution: vi.fn(),
      report: vi.fn(),
      insights: vi.fn(),
    },
  };
});

import { analyticsApi } from "../../api/client";
import AnalyticsPage from "./AnalyticsPage";

const funnelMock = vi.mocked(analyticsApi.funnel);
const reportMock = vi.mocked(analyticsApi.report);
const insightsMock = vi.mocked(analyticsApi.insights);

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <AnalyticsPage />
    </I18nextProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  funnelMock.mockResolvedValue({
    steps: ["App Opened", "Transfer"],
    step_counts: [100, 40],
    step_conversion: [1.0, 0.4],
    drop_off: [0, 60],
    overall_conversion: 0.4,
  });
  reportMock.mockResolvedValue({
    window_days: 7,
    active_users: 123,
    customer_ids: ["u1", "u2"],
  });
  insightsMock.mockResolvedValue({
    insights: [
      {
        index: 4,
        label: "4",
        value: 42,
        direction: "up",
        z_score: 2.3,
        pct_change: 4.25,
        notable: true,
        narrative: "4: spiked to 42 (+425% vs prior); 2.3σ from mean 14",
      },
    ],
  });
});

describe("AnalyticsPage", () => {
  it("computes a funnel with the steps and renders the step table", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /compute funnel/i }));

    await waitFor(() => expect(funnelMock).toHaveBeenCalledTimes(1));
    expect(funnelMock.mock.calls[0][0]).toMatchObject({
      steps: ["App Opened", "Transfer"],
      cross_product: false,
    });

    // step table renders the counts / conversion / drop-off
    expect(await screen.findByText("Drop-off")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("60")).toBeInTheDocument(); // drop-off
  });

  it("runs a report via the reports select", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("tab", { name: /reports/i }));
    await user.click(screen.getByRole("button", { name: /run report/i }));

    await waitFor(() => expect(reportMock).toHaveBeenCalledTimes(1));
    expect(reportMock.mock.calls[0][0]).toBe("active_users");
    expect(await screen.findByText("123")).toBeInTheDocument();
  });

  it("detects insights from a numeric series and lists the narrative", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("tab", { name: /auto-insights/i }));
    await user.click(screen.getByRole("button", { name: /detect/i }));

    await waitFor(() => expect(insightsMock).toHaveBeenCalledTimes(1));
    const body = insightsMock.mock.calls[0][0];
    expect(body.series).toEqual([10, 11, 9, 10, 42, 8, 10]);
    expect(await screen.findByText(/spiked to 42/)).toBeInTheDocument();
  });
});
