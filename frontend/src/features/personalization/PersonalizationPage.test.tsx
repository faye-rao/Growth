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
  personalizationApi: {
    register: vi.fn(),
    publish: vi.fn(),
    fetch: vi.fn(),
  },
}));

import { personalizationApi } from "../../api/client";
import PersonalizationPage from "./PersonalizationPage";

const registerMock = vi.mocked(personalizationApi.register);
const publishMock = vi.mocked(personalizationApi.publish);
const fetchMock = vi.mocked(personalizationApi.fetch);

function renderPage() {
  return render(
    <I18nextProvider i18n={i18n}>
      <PersonalizationPage />
    </I18nextProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  registerMock.mockResolvedValue({ key: "ok" });
  publishMock.mockResolvedValue({ ok: true });
  fetchMock.mockResolvedValue({ experiences: {} });
});

// Register an experience with the given key. Adds one en + one ar payload pair
// to the first variation (A) so we can assert the assembled multilingual payload.
async function registerExperience(
  user: ReturnType<typeof userEvent.setup>,
  key: string,
) {
  await user.type(screen.getByLabelText("experience-key"), key);

  // First variation (A) card is the first .ant-card with a variation-name input.
  const nameInputs = screen
    .getAllByRole("textbox")
    .filter((el) => el.getAttribute("aria-label")?.startsWith("variation-name-"));
  const varAKey = nameInputs[0]
    .getAttribute("aria-label")!
    .replace("variation-name-", "");
  // Scope all subsequent queries to variation A's card so tabs/labels from
  // variation B don't collide.
  const cardA = nameInputs[0].closest(".ant-card") as HTMLElement;
  const inA = within(cardA);

  // EN tab is active by default — add an en key/value pair.
  await user.click(inA.getByLabelText(`add-kv-${varAKey}-en`));
  let kInput = inA.getByLabelText((label: string) =>
    label.startsWith(`payload-key-${varAKey}-en-`),
  );
  let vInput = inA.getByLabelText((label: string) =>
    label.startsWith(`payload-val-${varAKey}-en-`),
  );
  await user.type(kInput, "title");
  await user.type(vInput, "Hello");

  // Switch to AR tab and add an ar pair.
  await user.click(inA.getByRole("tab", { name: "AR" }));
  await user.click(inA.getByLabelText(`add-kv-${varAKey}-ar`));
  kInput = inA.getByLabelText((label: string) =>
    label.startsWith(`payload-key-${varAKey}-ar-`),
  );
  vInput = inA.getByLabelText((label: string) =>
    label.startsWith(`payload-val-${varAKey}-ar-`),
  );
  await user.type(kInput, "title");
  await user.type(vInput, "مرحبا");

  await user.click(screen.getByRole("button", { name: /register experience/i }));
}

describe("PersonalizationPage", () => {
  it("registers an experience with assembled multilingual variations", async () => {
    const user = userEvent.setup();
    renderPage();

    await registerExperience(user, "home_banner");

    await waitFor(() => expect(registerMock).toHaveBeenCalledTimes(1));
    const body = registerMock.mock.calls[0][0];
    expect(body.key).toBe("home_banner");
    expect(body.control_pct).toBeCloseTo(0.1);
    // default audience spec = KYC users
    expect(body.audience_spec.match).toMatchObject({
      type: "attribute",
      field: "kyc_verified",
    });
    // two variations (A, B); A carries the multilingual payload we entered.
    expect(body.variations).toHaveLength(2);
    expect(body.variations[0]).toMatchObject({
      name: "A",
      weight: 1,
      payload: { en: { title: "Hello" }, ar: { title: "مرحبا" } },
    });
    // B has no pairs -> empty payload object
    expect(body.variations[1].payload).toEqual({});

    // appears in the list as a draft
    const row = screen.getByRole("row", { name: /home_banner/ });
    expect(within(row).getByText("draft")).toBeInTheDocument();
  });

  it("publishes a registered experience", async () => {
    const user = userEvent.setup();
    renderPage();

    await registerExperience(user, "home_banner");
    await waitFor(() => expect(registerMock).toHaveBeenCalledTimes(1));

    await user.click(screen.getByLabelText("publish-home_banner"));

    await waitFor(() => expect(publishMock).toHaveBeenCalledTimes(1));
    expect(publishMock).toHaveBeenCalledWith("home_banner");

    const row = screen.getByRole("row", { name: /home_banner/ });
    await waitFor(() =>
      expect(within(row).getByText("published")).toBeInTheDocument(),
    );
  });

  it("fetch tester calls fetch and renders the returned payload", async () => {
    const user = userEvent.setup();
    renderPage();

    // register so the experience-keys select has an option
    await registerExperience(user, "home_banner");
    await waitFor(() => expect(registerMock).toHaveBeenCalledTimes(1));

    fetchMock.mockResolvedValueOnce({
      experiences: { home_banner: { en: { title: "Hello" } } },
    });

    await user.type(screen.getByLabelText("customer-id"), "cust_123");

    // open the multi-select and pick home_banner
    await user.click(screen.getByRole("combobox", { name: "experience-keys" }));
    await user.click(await screen.findByRole("option", { name: "home_banner" }));

    await user.click(screen.getByRole("button", { name: /^fetch$/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const body = fetchMock.mock.calls[0][0];
    expect(body.identifiers).toEqual({ customer_id: "cust_123" });
    expect(body.experience_keys).toEqual(["home_banner"]);
    expect(body.locale).toBe("en");

    // returned payload JSON is rendered
    const json = await screen.findByLabelText("result-json-home_banner");
    expect(json.textContent).toContain("\"title\": \"Hello\"");
  });

  it("renders 'no content' for a null payload (control / miss / unpublished)", async () => {
    const user = userEvent.setup();
    renderPage();

    await registerExperience(user, "home_banner");
    await waitFor(() => expect(registerMock).toHaveBeenCalledTimes(1));

    fetchMock.mockResolvedValueOnce({ experiences: { home_banner: null } });

    await user.type(screen.getByLabelText("customer-id"), "cust_123");
    await user.click(screen.getByRole("combobox", { name: "experience-keys" }));
    await user.click(await screen.findByRole("option", { name: "home_banner" }));
    await user.click(screen.getByRole("button", { name: /^fetch$/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(
      await screen.findByLabelText("result-empty-home_banner"),
    ).toBeInTheDocument();
  });

  it("blocks register when the key is empty", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: /register experience/i }));
    expect(await screen.findByText(/experience key is required/i)).toBeInTheDocument();
    expect(registerMock).not.toHaveBeenCalled();
  });
});
