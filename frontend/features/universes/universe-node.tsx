"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { useRouter } from "next/navigation";

export type UniverseNodeData = {
  label: string;
  subtitle: string;
  year: number;
  accent: string;
  href: string;
  blocked: boolean;
};

export type UniverseGraphNode = Node<UniverseNodeData, "universe">;

export function UniverseNode({ data }: NodeProps<UniverseGraphNode>) {
  const router = useRouter();
  return (
    <div
      className="flow-universe"
      style={{ "--node-accent": data.accent } as React.CSSProperties}
    >
      <Handle type="target" position={Position.Top} aria-hidden="true" />
      <button type="button" onClick={() => router.push(data.href)}>
        <span className="flow-kicker">
          {data.blocked ? "Decision waiting" : `Current year ${data.year}`}
        </span>
        <strong>{data.label}</strong>
        <small>{data.subtitle}</small>
        <span className="flow-open">Open universe →</span>
      </button>
      <Handle type="source" position={Position.Bottom} aria-hidden="true" />
    </div>
  );
}
