import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
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

// Mock the API client (keep tests offline).
vi.mock("../../api/client", () => ({
  dataApi: {
    dqc: vi.fn(),
    resolve: vi.fn(),
    suppressionCheck: vi.fn(),
    ingest: vi.fn(),
  },
}));

import { dataApi } from "../../api/client";
import DataPage from "./DataPage";

const dqcMock = vi.mocked(dataApi.dqc);
const resolveMock = vi.mocked(dataApi.resolve);
const suppressionMock = vi.mocked(dataApi.suppressionCheck);

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <DataPage />
    </I18nextProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  dqcMock.mockResolvedValue({
    ok: false,
    metrics: {
      user_count: 5,
      event_count: 12,
      null_rate: 0.2,
      dup_rate: 0.0,
      latency_hours: 3,
    },
    alerts: [{ check: "null_rate", value: 0.2, threshold: 0.0 }],
  });
  resolveMock.mockResolvedValue({ canonical_id: "w1", resolved: true });
  suppressionMock.mockResolvedValue({
    allowed: ["w2", "w3"],
    suppressed: ["w1"],
  });
});

describe("DataPage", () => {
  it("loads the DQC report on mount and renders checks + alerts", async () => {
    renderPage();
    await waitFor(() => expect(dqcMock).toHaveBeenCalledTimes(1));

    // checks rendered as table rows (metric names); null_rate also appears in alerts
    expect((await screen.findAllByText("null_rate")).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("dup_rate")).toBeInTheDocument();
    expect(screen.getByText("latency_hours")).toBeInTheDocument();

    // pass/fail tags present
    expect(screen.getAllByText("fail").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("pass").length).toBeGreaterThanOrEqual(1);

    // alerts list populated
    const alerts = screen.getByLabelText("dqc-alerts");
    expect(within(alerts).getByText("null_rate")).toBeInTheDocument();
  });

  it("resolves an identity and shows the canonical id", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(dqcMock).toHaveBeenCalledTimes(1));

    await user.type(screen.getByLabelText("resolve-phone"), "971500000001");
    await user.click(screen.getByRole("button", { name: /^resolve$/i }));

    await waitFor(() => expect(resolveMock).toHaveBeenCalledTimes(1));
    expect(resolveMock).toHaveBeenCalledWith({ phone: "971500000001" });

    const result = screen.getByLabelText("resolve-result");
    expect(within(result).getByText("w1")).toBeInTheDocument();
  });

  it("runs a suppression check and shows the kept/suppressed partition", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(dqcMock).toHaveBeenCalledTimes(1));

    await user.type(screen.getByLabelText("suppression-ids"), "w1, w2, w3");
    await user.click(screen.getByRole("button", { name: /^check$/i }));

    await waitFor(() => expect(suppressionMock).toHaveBeenCalledTimes(1));
    expect(suppressionMock).toHaveBeenCalledWith(["w1", "w2", "w3"]);

    const result = screen.getByLabelText("suppression-result");
    expect(within(result).getByText("w2")).toBeInTheDocument();
    expect(within(result).getByText("w3")).toBeInTheDocument();
    expect(within(result).getByText("w1")).toBeInTheDocument();
  });
});
