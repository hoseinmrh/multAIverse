import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UniverseDetail } from "@/features/universes/universe-detail";
import { event, snapshot, universe } from "@/tests/fixtures";
import { renderWithQuery } from "@/tests/utils";

const {
  universeState,
  timeline,
  events,
  artifacts,
  generateUniverses,
  eventDetail,
} = vi.hoisted(() => ({
  universeState: vi.fn(),
  timeline: vi.fn(),
  events: vi.fn(),
  artifacts: vi.fn(),
  generateUniverses: vi.fn(),
  eventDetail: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  api: {
    universeState,
    timeline,
    events,
    artifacts,
    generateUniverses,
    event: eventDetail,
    advance: vi.fn(),
    selectChoice: vi.fn(),
    resetUniverse: vi.fn(),
  },
}));

describe("legacy custom-story event repair", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    universeState.mockResolvedValue({
      universe: {
        ...universe,
        name: "Become a Content Creator",
        starting_direction: "Become a Content Creator",
        status: "blocked",
      },
      state: {
        ...snapshot,
        career_title: "Content Creator",
        active_flags: ["startup_path", "creator_path"],
      },
    });
    timeline.mockResolvedValue({
      items: [snapshot],
      pagination: { offset: 0, limit: 100, total: 1, has_more: false },
    });
    events.mockResolvedValue({
      items: [
        {
          ...event,
          narrative_key: "startup-founder-role",
          title: "The company outgrows one founder's job",
        },
      ],
      pagination: { offset: 0, limit: 100, total: 1, has_more: false },
    });
    artifacts.mockResolvedValue({
      items: [],
      pagination: { offset: 0, limit: 100, total: 0, has_more: false },
    });
    generateUniverses.mockResolvedValue({ generated: false, universes: [] });
  });

  it("refreshes a demo-template event before displaying its decision", async () => {
    renderWithQuery(
      <UniverseDetail
        universeId={universe.id}
        scenarioId={universe.scenario_id}
      />,
    );

    await waitFor(() =>
      expect(generateUniverses).toHaveBeenCalledWith(universe.scenario_id),
    );
    expect(eventDetail).not.toHaveBeenCalled();
    expect(
      await screen.findByText(
        "This decision was refreshed for the current story.",
      ),
    ).toBeInTheDocument();
  });
});
