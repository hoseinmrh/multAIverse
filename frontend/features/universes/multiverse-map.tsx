"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { useQueries } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/async-state";
import {
  UniverseNode,
  type UniverseGraphNode,
} from "@/features/universes/universe-node";
import { api } from "@/lib/api/client";
import { useScenario } from "@/lib/api/queries";
import type { Event } from "@/lib/api/schemas";
import { universeAccent } from "@/lib/constants";

type RealityNode = Node<{ year: number }, "reality">;
type EventGraphNode = Node<
  {
    title: string;
    year: number;
    category: string;
    pending: boolean;
    accent: string;
  },
  "event"
>;
type MultiverseNode = RealityNode | UniverseGraphNode | EventGraphNode;

function RealityNode({ data }: NodeProps<RealityNode>) {
  return (
    <div className="flow-reality">
      <Handle type="source" position={Position.Bottom} aria-hidden="true" />
      <span>Current reality</span>
      <strong>{data.year}</strong>
      <small>The decision point</small>
    </div>
  );
}

function EventNode({ data }: NodeProps<EventGraphNode>) {
  return (
    <div
      className={`flow-event ${data.pending ? "flow-event-pending" : ""}`}
      style={{ "--node-accent": data.accent } as React.CSSProperties}
      tabIndex={0}
      aria-label={`${data.year}: ${data.title}${data.pending ? ", decision pending" : ""}`}
    >
      <Handle type="target" position={Position.Top} aria-hidden="true" />
      <span>{data.year}</span>
      <strong>{data.title}</strong>
      <small>{data.pending ? "Choice required" : data.category}</small>
      <Handle type="source" position={Position.Bottom} aria-hidden="true" />
    </div>
  );
}

const nodeTypes = {
  reality: RealityNode,
  universe: UniverseNode,
  event: EventNode,
};

export function MultiverseMap({ scenarioId }: { scenarioId: string }) {
  const scenario = useScenario(scenarioId);
  const universeIds =
    scenario.data?.universes.map((universe) => universe.id) ?? [];
  const eventQueries = useQueries({
    queries: universeIds.map((id) => ({
      queryKey: ["universe", id, "events"],
      queryFn: () => api.events(id),
    })),
  });

  const graph = useMemo(() => {
    if (!scenario.data)
      return { nodes: [] as MultiverseNode[], edges: [] as Edge[] };
    const nodes: MultiverseNode[] = [
      {
        id: "reality",
        type: "reality",
        position: { x: 530, y: 20 },
        data: { year: 2026 },
        draggable: false,
      },
    ];
    const edges: Edge[] = [];

    scenario.data.universes.forEach((universe, universeIndex) => {
      const accent = universeAccent(universe.visual_theme, universeIndex);
      const x = 90 + universeIndex * 440;
      const universeNodeId = `universe-${universe.id}`;
      const events = eventQueries[universeIndex]?.data?.items ?? [];
      nodes.push({
        id: universeNodeId,
        type: "universe",
        position: { x, y: 210 },
        data: {
          label: universe.name,
          subtitle: universe.subtitle,
          year: universe.current_year,
          accent,
          href: `/universe/${universe.id}?scenario=${scenarioId}`,
          blocked:
            universe.status === "blocked" ||
            events.some((event) => event.status === "pending"),
        },
        draggable: false,
      });
      edges.push({
        id: `reality-${universe.id}`,
        source: "reality",
        target: universeNodeId,
        animated: true,
        style: { stroke: accent, strokeWidth: 2 },
      });

      events.forEach((event: Event, eventIndex: number) => {
        const eventNodeId = `event-${event.id}`;
        nodes.push({
          id: eventNodeId,
          type: "event",
          position: {
            x: x + (eventIndex % 2 ? 36 : 0),
            y: 430 + eventIndex * 145,
          },
          data: {
            title: event.title,
            year: event.year,
            category: event.category,
            pending: event.status === "pending",
            accent,
          },
          draggable: false,
        });
        edges.push({
          id: `${universe.id}-${event.id}`,
          source:
            eventIndex === 0
              ? universeNodeId
              : `event-${events[eventIndex - 1]?.id}`,
          target: eventNodeId,
          style: { stroke: accent, strokeOpacity: 0.65 },
        });
      });
    });
    return { nodes, edges };
  }, [eventQueries, scenario.data, scenarioId]);

  if (scenario.isPending)
    return <LoadingState label="Charting the multiverse…" />;
  if (scenario.isError)
    return (
      <ErrorState
        error={scenario.error}
        onRetry={() => void scenario.refetch()}
      />
    );
  if (!scenario.data?.universes.length)
    return (
      <EmptyState
        title="No universes yet"
        message="Generate three branches from a scenario to reveal this map."
      />
    );

  return (
    <section className="map-page" aria-labelledby="map-title">
      <header className="map-header">
        <div>
          <p className="eyebrow">
            {scenario.data.scenario.simulation_mode} simulation
          </p>
          <h1 id="map-title">{scenario.data.scenario.title}</h1>
          <p>{scenario.data.scenario.decision_question}</p>
        </div>
        <div className="map-actions">
          <Link
            className="button button-secondary"
            href={`/compare/${scenarioId}`}
          >
            Compare universes
          </Link>
          <Link className="button button-ghost" href="/onboarding">
            New story
          </Link>
        </div>
      </header>
      {eventQueries.some((query) => query.isError) ? (
        <p className="inline-warning" role="status">
          Some yearly event nodes could not load. Universe cards remain
          available.
        </p>
      ) : null}
      <div
        className="flow-canvas"
        role="application"
        aria-label="Interactive multiverse map"
      >
        <ReactFlow
          nodes={graph.nodes}
          edges={graph.edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
          minZoom={0.35}
          maxZoom={1.4}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={28}
            size={1}
            color="#34405f"
          />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) =>
              typeof node.data?.accent === "string"
                ? node.data.accent
                : "#7686a8"
            }
            maskColor="rgba(5, 8, 18, 0.72)"
          />
        </ReactFlow>
      </div>
      <p className="map-help">
        Drag to pan · scroll or use controls to zoom · tab to a universe and
        press Enter
      </p>
    </section>
  );
}
