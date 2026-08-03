import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BackendStatus } from "@/components/backend-status";
import { renderWithQuery } from "@/tests/utils";

const config = {
  app_name: "Multiverse API",
  app_version: "0.1.0",
  narrative_provider: "mock",
  narrative_provider_status: {
    active_provider: "mock",
    state: "ready",
    model: null,
    fallback_enabled: false,
    detail: "Offline deterministic narrative generation is ready.",
  },
  simulation_modes: ["realistic", "cinematic", "utopian", "dark", "chaos"],
  max_universe_branches: 3,
  fictional_simulation_disclaimer: "Fictional only.",
};

describe("BackendStatus", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("reports when the offline narrative backend is healthy", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: true, status: 200, json: async () => config }),
    );
    renderWithQuery(<BackendStatus />);
    expect(screen.getByText("Checking local backend…")).toBeInTheDocument();
    expect(
      await screen.findByText("Offline narrative ready"),
    ).toBeInTheDocument();
  });

  it("shows a recoverable unavailable state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("connection refused")),
    );
    renderWithQuery(<BackendStatus />);
    expect(
      await screen.findByText("Local backend unavailable"),
    ).toBeInTheDocument();
  });
});
