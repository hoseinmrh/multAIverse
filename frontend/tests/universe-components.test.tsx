import { ReactFlowProvider } from "@xyflow/react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EventDecisionModal } from "@/features/universes/event-decision-modal";
import { StatisticCard } from "@/features/universes/stat-card";
import { Timeline } from "@/features/universes/timeline";
import { UniverseNode } from "@/features/universes/universe-node";
import { event, eventDetail, snapshot } from "@/tests/fixtures";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

describe("universe components", () => {
  it("renders an accessible, clickable universe node", () => {
    render(
      <ReactFlowProvider>
        <UniverseNode
          id="node"
          type="universe"
          selected={false}
          dragging={false}
          draggable={false}
          selectable
          deletable={false}
          isConnectable={false}
          zIndex={0}
          positionAbsoluteX={0}
          positionAbsoluteY={0}
          data={{
            label: "Applied AI Leader",
            subtitle: "Responsible systems",
            year: 2027,
            accent: "#3B82F6",
            href: "/universe/1",
            blocked: true,
          }}
        />
      </ReactFlowProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Applied AI Leader/i }));
    expect(push).toHaveBeenCalledWith("/universe/1");
    expect(screen.getByText("Decision waiting")).toBeInTheDocument();
  });

  it("shows statistic values with a semantic meter", () => {
    render(<StatisticCard label="Happiness" value={71} />);
    expect(screen.getByRole("meter", { name: "Happiness" })).toHaveAttribute(
      "aria-valuenow",
      "71",
    );
    expect(screen.getByText("71")).toBeInTheDocument();
  });

  it("renders timeline snapshots and pending events", () => {
    render(<Timeline snapshots={[snapshot]} events={[event]} />);
    expect(screen.getByText("2026")).toBeInTheDocument();
    expect(screen.getByText("The leadership offer")).toBeInTheDocument();
    expect(screen.getByText("Decision waiting")).toBeInTheDocument();
  });

  it("requires and confirms a server-provided event choice", () => {
    const onConfirm = vi.fn();
    render(
      <EventDecisionModal
        detail={eventDetail}
        isSubmitting={false}
        onConfirm={onConfirm}
      />,
    );
    expect(
      screen.getByRole("dialog", { name: "The leadership offer" }),
    ).toBeInTheDocument();
    expect(screen.getByText("+7 career level")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/Choose the measured route/i));
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm this choice" }),
    );
    expect(onConfirm).toHaveBeenCalledWith(eventDetail.choices[1]?.id);
  });
});
