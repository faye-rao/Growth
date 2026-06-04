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
  campaignApi: { run: vi.fn() },
  audienceApi: { size: vi.fn() },
}));

import { campaignApi, audienceApi } from "../../api/client";
import CampaignPage from "./CampaignPage";

const runMock = vi.mocked(campaignApi.run);
const sizeMock = vi.mocked(audienceApi.size);

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <CampaignPage />
    </I18nextProvider>,
  );
}

async function openWizard(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /new campaign/i }));
}

beforeEach(() => {
  vi.clearAllMocks();
  runMock.mockResolvedValue({
    campaign_id: "cmp_test",
    audience_size: 100,
    eligible_size: 100,
    sent_by_variant: { A: 40, B: 41 },
    control_count: 10,
    capped_count: 5,
    not_sent_count: 4,
  });
  sizeMock.mockResolvedValue({ size: 1234 });
});

describe("CampaignPage wizard", () => {
  it("advances through the 3 steps and estimates audience size", async () => {
    const user = userEvent.setup();
    renderPage();
    await openWizard(user);

    // Step 1 — audience
    expect(screen.getByText("Target users")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /estimate size/i }));
    await waitFor(() => expect(sizeMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("1,234")).toBeInTheDocument();

    // -> Step 2 — content
    await user.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByText("Content (A/B/N)")).toBeInTheDocument();

    // -> Step 3 — schedule
    await user.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByText("Schedule & goals")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^run$/i })).toBeInTheDocument();
  });

  it("adds and removes a variant row", async () => {
    const user = userEvent.setup();
    renderPage();
    await openWizard(user);
    await user.click(screen.getByRole("button", { name: /^next$/i }));

    // default state has 2 variants (A, B)
    expect(screen.getByLabelText("variant-name-v1")).toHaveValue("A");
    expect(screen.getByLabelText("variant-name-v2")).toHaveValue("B");

    await user.click(screen.getByRole("button", { name: /add variant/i }));
    // a 3rd name input now exists
    const nameInputs = screen
      .getAllByRole("textbox")
      .filter((el) => el.getAttribute("aria-label")?.startsWith("variant-name-"));
    expect(nameInputs).toHaveLength(3);

    // remove the first variant (A)
    await user.click(screen.getByLabelText("remove-variant-v1"));
    expect(screen.queryByLabelText("variant-name-v1")).not.toBeInTheDocument();
    const after = screen
      .getAllByRole("textbox")
      .filter((el) => el.getAttribute("aria-label")?.startsWith("variant-name-"));
    expect(after).toHaveLength(2);
  });

  it("runs the campaign with an assembled request and renders the summary", async () => {
    const user = userEvent.setup();
    renderPage();
    await openWizard(user);

    // step 1 -> 2
    await user.click(screen.getByRole("button", { name: /^next$/i }));
    // confirm the control_pct field reflects the wizard default
    expect(screen.getByLabelText("control-pct")).toHaveValue("0.10");
    // step 2 -> 3
    await user.click(screen.getByRole("button", { name: /^next$/i }));

    await user.click(screen.getByRole("button", { name: /^run$/i }));

    await waitFor(() => expect(runMock).toHaveBeenCalledTimes(1));
    const req = runMock.mock.calls[0][0];
    expect(req.variants).toEqual([
      { name: "A", weight: 1, content_id: "content_a" },
      { name: "B", weight: 1, content_id: "content_b" },
    ]);
    expect(req.control_pct).toBeCloseTo(0.1);
    expect(req.channel).toBe("push");
    expect(req.schedule?.trigger_type).toBe("batch");

    // summary renders
    expect(await screen.findByText("Run result")).toBeInTheDocument();
    expect(screen.getByText("Total sent")).toBeInTheDocument();
    // 81 appears both in the result panel and the freshly-added list row
    expect(screen.getAllByText("81").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Control held out")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument(); // control
    expect(screen.getByText("Frequency capped")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument(); // capped
    expect(screen.getByText("Not sent (suppressed)")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument(); // not sent

    // launched campaign now appears in the list after Done (id is generated client-side)
    await user.click(screen.getByRole("button", { name: /^done$/i }));
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText(/^cmp_\d+$/)).toBeInTheDocument();
  });

  it("blocks Run / advancing when there are zero variants", async () => {
    const user = userEvent.setup();
    renderPage();
    await openWizard(user);
    await user.click(screen.getByRole("button", { name: /^next$/i }));

    // remove both variants
    await user.click(screen.getByLabelText("remove-variant-v1"));
    await user.click(screen.getByLabelText("remove-variant-v2"));

    // try to advance to step 3 — should be blocked (still on Content step)
    await user.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByText("Content (A/B/N)")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^run$/i })).not.toBeInTheDocument();
    // validation message surfaced
    expect(await screen.findByText(/at least one variant/i)).toBeInTheDocument();
    expect(runMock).not.toHaveBeenCalled();
  });
});
