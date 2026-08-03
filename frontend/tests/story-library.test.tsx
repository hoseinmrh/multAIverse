import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "@/components/app-shell";
import { StoryLibrary } from "@/features/scenarios/story-library";
import { renderWithQuery } from "@/tests/utils";

const { profiles, scenarios, generateUniverses, push } = vi.hoisted(() => ({
  profiles: vi.fn(),
  scenarios: vi.fn(),
  generateUniverses: vi.fn(),
  push: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  api: { profiles, scenarios, generateUniverses },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const originalProfileId = "10000000-0000-4000-8000-000000000001";
const newProfileId = "10000000-0000-4000-8000-000000000002";
const originalScenarioId = "20000000-0000-4000-8000-000000000001";
const newScenarioId = "20000000-0000-4000-8000-000000000002";

function profile(id: string, name: string) {
  return {
    id,
    name,
    birth_year: 1995,
    starting_year: 2026,
    starting_age: 31,
    location: "Milan",
    occupation: "Engineer",
    education: "MSc",
    biography: "",
    strengths: [],
    weaknesses: [],
    interests: [],
    goals: [],
    constraints: [],
    starting_stats: {},
    created_at: "2026-08-03T10:00:00Z",
    updated_at: "2026-08-03T10:00:00Z",
  };
}

function scenario(id: string, profileId: string, title: string) {
  return {
    id,
    profile_id: profileId,
    title,
    decision_question: `What should ${title} prioritize next?`,
    description: "Three possible paths",
    number_of_universes: 3,
    simulation_mode: "realistic",
    seed: 123,
    created_at: "2026-08-03T10:05:00Z",
  };
}

describe("saved story navigation", () => {
  beforeEach(() => {
    profiles.mockReset();
    scenarios.mockReset();
    generateUniverses.mockReset();
    push.mockReset();
    generateUniverses.mockResolvedValue({ generated: false, universes: [] });
    profiles.mockResolvedValue({
      items: [
        profile(originalProfileId, "Original person"),
        profile(newProfileId, "New person"),
      ],
      pagination: { offset: 0, limit: 100, total: 2, has_more: false },
    });
    scenarios.mockResolvedValue({
      items: [
        scenario(originalScenarioId, originalProfileId, "Original story"),
        scenario(newScenarioId, newProfileId, "New story"),
      ],
      pagination: { offset: 0, limit: 100, total: 2, has_more: false },
    });
  });

  it("prepares and opens the selected person's scenario ID", async () => {
    renderWithQuery(<StoryLibrary />);

    expect(
      await screen.findByRole("heading", { name: "New person" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Original person" }),
    ).toBeInTheDocument();
    const openButtons = screen.getAllByRole("button", {
      name: "Open three universes",
    });
    fireEvent.click(openButtons[1]!);
    await waitFor(() =>
      expect(generateUniverses).toHaveBeenCalledWith(newScenarioId),
    );
    expect(push).toHaveBeenCalledWith(`/multiverse/${newScenarioId}`);
    expect(
      screen.getAllByRole("link", { name: "New scenario" })[1],
    ).toHaveAttribute("href", `/scenario?profile=${newProfileId}`);
  });

  it("uses library navigation instead of hardcoding the demo scenario", () => {
    renderWithQuery(
      <AppShell>
        <p>Current page</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "Stories" })).toHaveAttribute(
      "href",
      "/stories",
    );
    expect(screen.queryByRole("link", { name: "Map" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Compare" }),
    ).not.toBeInTheDocument();
  });
});
