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

// Mock the API client (keep tests offline).
vi.mock("../../api/client", () => ({
  experimentApi: { split: vi.fn(), report: vi.fn() },
}));

import { experimentApi } from "../../api/client";
import ExperimentPage from "./ExperimentPage";

const splitMock = vi.mocked(experimentApi.split);
const reportMock = vi.mocked(experimentApi.report);

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <ExperimentPage />
    </I18nextProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  // arm -> [ids] envelope
  splitMock.mockResolvedValue({
    assignments: {
      shadow: ["u1"],
      control: ["u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9", "u10"],
    },
  });
  reportMock.mockResolvedValue({
    control_sent: 10,
    control_conversions: 3,
    control_rate: 0.3,
    shadow_sent: 10,
    shadow_conversions: 4,
    shadow_rate: 0.4,
    absolute_lift: 0.1,
    relative_lift: 0.3333,
    z: -0.46,
    p_value: 0.64,
    significant: false,
    non_inferiority_margin: 0,
    verdict: "not_worse",
    diff_ci_low: -0.3,
    diff_ci_high: 0.5,
  });
});

describe("ExperimentPage — shadow split", () => {
  it("calls experimentApi.split with shadow_pct and renders arm counts", async () => {
    const user = userEvent.setup();
    renderPage();

    // default shadow_pct field is 0.05
    expect(screen.getByLabelText("shadow-pct")).toHaveValue("0.05");

    await user.click(screen.getByRole("button", { name: /^split$/i }));

    await waitFor(() => expect(splitMock).toHaveBeenCalledTimes(1));
    const arg = splitMock.mock.calls[0][0];
    expect(arg.shadow_pct).toBeCloseTo(0.05);
    expect(arg.customer_ids.length).toBe(10);

    // arm counts rendered: shadow=1, control=9
    expect(await screen.findByText("Shadow arm")).toBeInTheDocument();
    expect(screen.getByText("Control arm")).toBeInTheDocument();
    // shadow count 1 and control count 9 appear (statistics)
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("9").length).toBeGreaterThanOrEqual(1);
    // arm tag labels in the breakdown table
    expect(screen.getByText("shadow")).toBeInTheDocument();
    expect(screen.getByText("control")).toBeInTheDocument();
  });
});

describe("ExperimentPage — comparison report", () => {
  it("calls experimentApi.report and renders the verdict tag + rates", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /^compare$/i }));

    await waitFor(() => expect(reportMock).toHaveBeenCalledTimes(1));
    const arg = reportMock.mock.calls[0][0];
    expect(Array.isArray(arg.control_records)).toBe(true);
    expect(Array.isArray(arg.shadow_records)).toBe(true);
    expect(arg.control_records.length).toBe(10);
    expect(arg.non_inferiority_margin).toBe(0);

    // verdict tag (not_worse -> blue) rendered
    const tag = await screen.findByLabelText("verdict-tag");
    expect(tag).toHaveTextContent(/not worse/i);

    // rates rendered
    expect(screen.getByText("Control rate")).toBeInTheDocument();
    expect(screen.getByText("Shadow rate")).toBeInTheDocument();
    expect(screen.getByText("30.00%")).toBeInTheDocument(); // control_rate
    expect(screen.getByText("40.00%")).toBeInTheDocument(); // shadow_rate
    // significance + CI
    expect(screen.getByText("p-value")).toBeInTheDocument();
    expect(screen.getByText("Diff 95% CI")).toBeInTheDocument();
  });

  it("surfaces a JSON parse error without calling the API", async () => {
    const user = userEvent.setup();
    renderPage();

    const controlBox = screen.getByLabelText("control-records");
    await user.clear(controlBox);
    await user.type(controlBox, "not json");

    await user.click(screen.getByRole("button", { name: /^compare$/i }));

    expect(await screen.findByText(/Control records:/i)).toBeInTheDocument();
    expect(reportMock).not.toHaveBeenCalled();
  });
});
