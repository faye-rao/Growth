import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

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

// React Flow measures the container via ResizeObserver; jsdom lacks it.
if (!window.ResizeObserver) {
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}

import FlowCanvas, { serializeFlow, type FlowDefinition } from "./FlowCanvas";

function countNodes(): number {
  // React Flow renders each node with the .react-flow__node class.
  return document.querySelectorAll(".react-flow__node").length;
}

describe("FlowCanvas", () => {
  it("adds nodes from the palette (node count increases)", async () => {
    const user = userEvent.setup();
    render(<FlowCanvas />);

    expect(countNodes()).toBe(0);

    await user.click(screen.getByLabelText("add-node-entry"));
    await user.click(screen.getByLabelText("add-node-delay"));
    await user.click(screen.getByLabelText("add-node-webhook"));

    expect(countNodes()).toBe(3);

    // labels render on the canvas
    const canvas = screen.getByTestId("flow-canvas");
    expect(within(canvas).getByText("Entry")).toBeInTheDocument();
    expect(within(canvas).getByText("Delay")).toBeInTheDocument();
    expect(within(canvas).getByText("Webhook")).toBeInTheDocument();
  });

  it("exports a JSON flow definition containing the added node types", async () => {
    const user = userEvent.setup();
    const onExport = vi.fn();
    render(<FlowCanvas onExport={onExport} />);

    await user.click(screen.getByLabelText("add-node-entry"));
    await user.click(screen.getByLabelText("add-node-branch"));
    await user.click(screen.getByLabelText("add-node-ab_split"));
    await user.click(screen.getByLabelText("add-node-wait_event"));

    await user.click(screen.getByLabelText("export-flow"));

    // callback received a structured definition
    expect(onExport).toHaveBeenCalledTimes(1);
    const def = onExport.mock.calls[0][0] as FlowDefinition;
    const types = def.nodes.map((n) => n.type);
    expect(types).toEqual(["entry", "branch", "ab_split", "wait_event"]);
    expect(def.nodes).toHaveLength(4);
    expect(def.edges).toEqual([]);

    // and the JSON is rendered in the <pre> for the user
    const pre = screen.getByTestId("flow-export");
    const parsed = JSON.parse(pre.textContent ?? "{}") as FlowDefinition;
    expect(parsed.nodes.map((n) => n.type)).toContain("ab_split");
    expect(parsed.nodes.map((n) => n.type)).toContain("wait_event");
  });
});

describe("serializeFlow", () => {
  it("serializes nodes/edges into the flow definition shape", () => {
    const def = serializeFlow(
      [
        {
          id: "entry_1",
          type: "input",
          position: { x: 10.4, y: 20.6 },
          data: { label: "Entry", flowType: "entry" },
        },
        {
          id: "delay_2",
          type: "default",
          position: { x: 100, y: 200 },
          data: { label: "Delay", flowType: "delay" },
        },
      ],
      [{ id: "e1", source: "entry_1", target: "delay_2" }],
    );

    expect(def.nodes).toEqual([
      { id: "entry_1", type: "entry", label: "Entry", position: { x: 10, y: 21 } },
      { id: "delay_2", type: "delay", label: "Delay", position: { x: 100, y: 200 } },
    ]);
    expect(def.edges).toEqual([{ id: "e1", source: "entry_1", target: "delay_2" }]);
  });
});
