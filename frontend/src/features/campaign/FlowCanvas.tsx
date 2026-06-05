// Flow canvas (M3 orchestration): build a campaign flow out of nodes —
// entry / delay / branch / A·B split / wait-event / webhook — connected by edges.
// "Export flow" serializes the graph to a JSON flow definition.
import { useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type Connection,
} from "reactflow";
import "reactflow/dist/style.css";
import { Button, Space, Typography } from "antd";

const { Text } = Typography;

// The orchestration node kinds the Flow palette can drop onto the canvas.
export type FlowNodeType =
  | "entry"
  | "delay"
  | "branch"
  | "ab_split"
  | "wait_event"
  | "webhook";

const NODE_LABELS: Record<FlowNodeType, string> = {
  entry: "Entry",
  delay: "Delay",
  branch: "Branch",
  ab_split: "A/B Split",
  wait_event: "Wait Event",
  webhook: "Webhook",
};

// Palette order: entry first (start node), then orchestration steps.
const PALETTE: FlowNodeType[] = [
  "entry",
  "delay",
  "branch",
  "ab_split",
  "wait_event",
  "webhook",
];

// Serialized flow definition — the campaign flow payload an API would persist.
export interface FlowDefinition {
  nodes: Array<{
    id: string;
    type: FlowNodeType;
    label: string;
    position: { x: number; y: number };
  }>;
  edges: Array<{ id: string; source: string; target: string }>;
}

let nodeSeq = 0;
function nextNodeId(type: FlowNodeType): string {
  nodeSeq += 1;
  return `${type}_${nodeSeq}`;
}

export function serializeFlow(nodes: Node[], edges: Edge[]): FlowDefinition {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: (n.data?.flowType ?? "delay") as FlowNodeType,
      label: String(n.data?.label ?? ""),
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
    })),
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  };
}

export interface FlowCanvasProps {
  // Optional callback fired on "Export flow" with the serialized definition.
  onExport?: (def: FlowDefinition) => void;
}

export default function FlowCanvas({ onExport }: FlowCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node["data"]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [exported, setExported] = useState<FlowDefinition | null>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const addNode = useCallback(
    (type: FlowNodeType) => {
      const id = nextNodeId(type);
      setNodes((nds) => {
        // Stagger new nodes so they don't stack exactly on top of each other.
        const offset = nds.length * 60;
        return nds.concat({
          id,
          // entry is a source-only start node; others are default (in+out).
          type: type === "entry" ? "input" : "default",
          position: { x: 80 + (offset % 360), y: 60 + offset },
          data: { label: NODE_LABELS[type], flowType: type },
        });
      });
    },
    [setNodes],
  );

  const exportFlow = useCallback(() => {
    const def = serializeFlow(nodes, edges);
    setExported(def);
    onExport?.(def);
  }, [nodes, edges, onExport]);

  return (
    <div>
      <Space wrap style={{ marginBottom: 12 }}>
        <Text strong>Add node:</Text>
        {PALETTE.map((type) => (
          <Button
            key={type}
            size="small"
            aria-label={`add-node-${type}`}
            onClick={() => addNode(type)}
          >
            {NODE_LABELS[type]}
          </Button>
        ))}
        <Button
          type="primary"
          size="small"
          aria-label="export-flow"
          onClick={exportFlow}
        >
          Export flow
        </Button>
      </Space>

      <div
        data-testid="flow-canvas"
        style={{ width: "100%", height: 480, border: "1px solid #f0f0f0" }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodesDraggable
          nodesConnectable
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      {exported && (
        <pre
          data-testid="flow-export"
          aria-label="flow-export"
          style={{
            marginTop: 12,
            maxHeight: 240,
            overflow: "auto",
            background: "#fafafa",
            padding: 12,
            border: "1px solid #f0f0f0",
            borderRadius: 4,
          }}
        >
          {JSON.stringify(exported, null, 2)}
        </pre>
      )}
    </div>
  );
}
