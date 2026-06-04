import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "../../i18n";

// AntD's responsive Grid (Row/Col) calls window.matchMedia, which jsdom does not
// implement. Polyfill it for this suite (shared setup.ts is off-limits).
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

// Mock the API client so tests stay fully offline.
vi.mock("../../api/client", () => {
  return {
    audienceApi: {
      nl2sql: vi.fn(),
      size: vi.fn(),
      compile: vi.fn(),
      templates: vi.fn(),
      evaluate: vi.fn(),
    },
  };
});

import { audienceApi } from "../../api/client";
import AudiencePage from "./AudiencePage";

const mockApi = audienceApi as unknown as {
  nl2sql: ReturnType<typeof vi.fn>;
  size: ReturnType<typeof vi.fn>;
  compile: ReturnType<typeof vi.fn>;
  templates: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.clearAllMocks();
  mockApi.templates.mockResolvedValue({ templates: ["High-value KYC", "Dormant wallets"] });
  mockApi.size.mockResolvedValue({ size: 12345 });
  mockApi.nl2sql.mockResolvedValue({
    text: "kyc users",
    dsl: {
      match: {
        op: "and",
        children: [{ type: "attribute", field: "is_kyc", operator: "eq", value: true }],
      },
    },
    confidence: 0.92,
    matched: ["is_kyc"],
    unmatched: [],
    requires_review: true,
  });
});

describe("AudiencePage", () => {
  it("renders the translated title", async () => {
    render(<AudiencePage />);
    expect(
      await screen.findByText("Audience (Cohort Segmentation)"),
    ).toBeInTheDocument();
  });

  it("loads templates on mount", async () => {
    render(<AudiencePage />);
    expect(await screen.findByText("High-value KYC")).toBeInTheDocument();
    expect(mockApi.templates).toHaveBeenCalledTimes(1);
  });

  it("NL2SQL button calls nl2sql and renders confidence + review tag", async () => {
    const user = userEvent.setup();
    render(<AudiencePage />);

    const textarea = screen.getByLabelText("nl2sql-input");
    await user.type(textarea, "kyc users");

    const button = screen.getByRole("button", { name: /Translate/i });
    await user.click(button);

    await waitFor(() => expect(mockApi.nl2sql).toHaveBeenCalledWith("kyc users"));

    expect(await screen.findByTestId("nl-confidence")).toHaveTextContent("92%");
    expect(screen.getByText("Needs review")).toBeInTheDocument();
  });

  it("calls audienceApi.size and renders the number after loading a DSL", async () => {
    const user = userEvent.setup();
    render(<AudiencePage />);

    // Translate populates the builder with a non-empty rule, triggering size().
    await user.type(screen.getByLabelText("nl2sql-input"), "kyc users");
    await user.click(screen.getByRole("button", { name: /Translate/i }));

    await waitFor(() => expect(mockApi.size).toHaveBeenCalled());

    const sizeCard = await screen.findByTestId("audience-size");
    await waitFor(() =>
      expect(within(sizeCard.closest(".ant-statistic")!).getByText(/12,345/)).toBeInTheDocument(),
    );
  });
});
