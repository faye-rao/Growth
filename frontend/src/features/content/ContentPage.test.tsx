import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "../../i18n";

// AntD's responsive Grid (Row/Col) + Select call window.matchMedia, which jsdom
// does not implement. Polyfill it for this suite (shared setup.ts is off-limits).
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
    contentApi: {
      generate: vi.fn(),
      compliance: vi.fn(),
      selectBest: vi.fn(),
    },
  };
});

import { contentApi } from "../../api/client";
import ContentPage from "./ContentPage";

const mockApi = contentApi as unknown as {
  generate: ReturnType<typeof vi.fn>;
  compliance: ReturnType<typeof vi.fn>;
  selectBest: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.clearAllMocks();
  mockApi.generate.mockResolvedValue({
    variants: [
      {
        locale: "en",
        text: "Activate your Botim Wallet today and start sending money.",
        meta: { compliant: true, violations: [] },
      },
      {
        locale: "ar",
        text: "فعّل محفظة Wallet من بوتيم اليوم وابدأ تحويل الأموال.",
        meta: { compliant: true, violations: [] },
      },
    ],
  });
  mockApi.compliance.mockResolvedValue({
    ok: false,
    violations: ["banned_claim:guaranteed", "missing_disclaimer"],
    fixed_text: "Get your loan guaranteed approval T&Cs apply.",
  });
  mockApi.selectBest.mockResolvedValue({ best: "copy_A" });
});

describe("ContentPage", () => {
  it("renders the title", async () => {
    render(<ContentPage />);
    expect(await screen.findByText(/Content \(M6\)/i)).toBeInTheDocument();
  });

  it("Generate calls contentApi.generate with locales/n and renders variants", async () => {
    const user = userEvent.setup();
    render(<ContentPage />);

    // Defaults: goal=activate_wallet, product=Wallet, locales=[en,ar], n=2.
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    await waitFor(() => expect(mockApi.generate).toHaveBeenCalled());
    const arg = mockApi.generate.mock.calls[0][0];
    expect(arg.locales).toEqual(["en", "ar"]);
    expect(arg.n).toBe(2);
    expect(arg.goal).toBe("activate_wallet");
    expect(arg.product).toBe("Wallet");

    // Variants render, grouped by locale, with compliant tags.
    const variants = await screen.findByTestId("variants");
    expect(
      within(variants).getByText(/Activate your Botim Wallet today/i),
    ).toBeInTheDocument();
    expect(within(variants).getByText(/فعّل محفظة/)).toBeInTheDocument();
    expect(within(variants).getAllByText("compliant").length).toBe(2);
  });

  it("renders Arabic variant text with RTL direction", async () => {
    const user = userEvent.setup();
    render(<ContentPage />);
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    const ar = await screen.findByText(/فعّل محفظة/);
    expect(ar).toHaveAttribute("dir", "rtl");
  });

  it("shows violation tags when a generated variant is non-compliant", async () => {
    mockApi.generate.mockResolvedValueOnce({
      variants: [
        {
          locale: "en",
          text: "Guaranteed approval!",
          meta: { compliant: false, violations: ["banned_claim:guaranteed"] },
        },
      ],
    });
    const user = userEvent.setup();
    render(<ContentPage />);
    await user.click(screen.getByRole("button", { name: /^Generate$/i }));

    expect(await screen.findByText("banned_claim:guaranteed")).toBeInTheDocument();
    expect(screen.getByText("non-compliant")).toBeInTheDocument();
  });

  it("Compliance calls contentApi.compliance and renders violations + fixed_text", async () => {
    const user = userEvent.setup();
    render(<ContentPage />);

    await user.type(
      screen.getByLabelText("compliance-text"),
      "Get your loan guaranteed approval",
    );
    await user.click(screen.getByRole("button", { name: /Check compliance/i }));

    await waitFor(() => expect(mockApi.compliance).toHaveBeenCalled());
    expect(mockApi.compliance.mock.calls[0][0].text).toBe(
      "Get your loan guaranteed approval",
    );

    const result = await screen.findByTestId("compliance-result");
    expect(within(result).getByText("not ok")).toBeInTheDocument();
    expect(within(result).getByText("banned_claim:guaranteed")).toBeInTheDocument();
    expect(within(result).getByText("missing_disclaimer")).toBeInTheDocument();

    const fixed = screen.getByTestId("fixed-text");
    expect(fixed).toHaveTextContent("T&Cs apply.");
    // fixed_text differs from input -> "changed" badge.
    expect(within(result).getByText("changed")).toBeInTheDocument();
  });

  it("Select best calls contentApi.selectBest and shows the winner", async () => {
    const user = userEvent.setup();
    render(<ContentPage />);

    await user.click(screen.getByRole("button", { name: /Select best/i }));

    await waitFor(() => expect(mockApi.selectBest).toHaveBeenCalled());
    expect(await screen.findByTestId("best-result")).toHaveTextContent("copy_A");
  });
});
