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
          narrative_provider_status: {
            active_provider: "mock",
            state: "ready",
            model: null,
            fallback_enabled: false,
            detail: "Offline deterministic narrative generation is ready.",
          },
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

  it("reports configured OpenAI and mock fallback states without credentials", () => {
    const base = {
      app_name: "Multiverse",
      app_version: "0.1.0",
      simulation_modes: ["realistic" as const],
      max_universe_branches: 3,
      fictional_simulation_disclaimer: "Fictional",
    };
    const { rerender } = render(
      <ProviderStatus
        config={{
          ...base,
          narrative_provider: "openai",
          narrative_provider_status: {
            active_provider: "openai",
            state: "configured",
            model: "configured-model",
            fallback_enabled: true,
            detail:
              "OpenAI structured narrative generation is configured with mock fallback.",
          },
        }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "OpenAI narrative provider",
    );
    expect(screen.getByRole("status")).toHaveTextContent("configured-model");
    expect(screen.getByRole("status")).toHaveTextContent(
      "GPT with mock fallback",
    );

    rerender(
      <ProviderStatus
        config={{
          ...base,
          narrative_provider: "openai",
          narrative_provider_status: {
            active_provider: "openai",
            state: "configured",
            model: "configured-model",
            fallback_enabled: false,
            detail:
              "OpenAI-only narrative generation is configured; failures preserve the current simulation state.",
          },
        }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("GPT only");

    rerender(
      <ProviderStatus
        config={{
          ...base,
          narrative_provider: "openai",
          narrative_provider_status: {
            active_provider: "mock",
            state: "fallback",
            model: null,
            fallback_enabled: true,
            detail:
              "OpenAI configuration is incomplete; the offline mock fallback is active.",
          },
        }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Mock fallback active",
    );
    expect(screen.getByRole("status")).toHaveTextContent("Fallback");
  });
});
