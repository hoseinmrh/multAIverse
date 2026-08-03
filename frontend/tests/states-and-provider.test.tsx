import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ErrorState, LoadingState } from "@/components/ui/async-state";
import { ProviderStatus } from "@/features/scenarios/provider-status";

describe("loading, failure, and provider states", () => {
  it("announces loading and offers a failure retry", () => {
    const retry = vi.fn();
    const { rerender } = render(<LoadingState label="Loading timeline…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading timeline…");
    rerender(
      <ErrorState error={new Error("Backend unavailable")} onRetry={retry} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Backend unavailable");
    expect(retry).toHaveBeenCalledOnce();
  });

  it("identifies the offline mock provider without exposing credentials", () => {
    render(
      <ProviderStatus
        config={{
          app_name: "Multiverse",
          app_version: "0.1.0",
          narrative_provider: "mock",
          simulation_modes: ["realistic"],
          max_universe_branches: 3,
          fictional_simulation_disclaimer: "Fictional",
        }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Mock narrative provider",
    );
    expect(screen.getByRole("status")).toHaveTextContent("No API key is used");
  });
});
