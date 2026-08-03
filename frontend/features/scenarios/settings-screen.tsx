"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useMotionPreference } from "@/app/providers";
import { ErrorState, LoadingState } from "@/components/ui/async-state";
import { ProviderStatus } from "@/features/scenarios/provider-status";
import { api } from "@/lib/api/client";
import { usePublicConfig } from "@/lib/api/queries";
import { DEMO_SCENARIO_ID } from "@/lib/constants";

export function SettingsScreen() {
  const config = usePublicConfig();
  const queryClient = useQueryClient();
  const { reducedMotion, setReducedMotion } = useMotionPreference();
  const [defaultMode, setDefaultMode] = useState("realistic");
  const [defaultHorizon, setDefaultHorizon] = useState(5);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const storedMode =
      window.localStorage.getItem("multiverse-default-mode") ?? "realistic";
    const storedHorizon = Number(
      window.localStorage.getItem("multiverse-default-horizon") ?? 5,
    );
    queueMicrotask(() => {
      setDefaultMode(storedMode);
      setDefaultHorizon(storedHorizon);
    });
  }, []);

  const resetDemo = useMutation({
    mutationFn: async () => {
      const scenario = await api.scenario(DEMO_SCENARIO_ID);
      await Promise.all(
        scenario.universes.map((universe) => api.resetUniverse(universe.id)),
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setNotice(
        "All three demo universes were reset to their seeded 2026 state.",
      );
    },
  });

  if (config.isPending)
    return <LoadingState label="Checking local configuration…" />;
  if (config.isError)
    return (
      <ErrorState error={config.error} onRetry={() => void config.refetch()} />
    );

  return (
    <section className="settings-page" aria-labelledby="settings-title">
      <header className="page-heading">
        <p className="eyebrow">Local control room</p>
        <h1 id="settings-title">Settings & provider status</h1>
        <p>
          Preferences live on this device. Simulation truth remains in the
          backend.
        </p>
      </header>

      {notice ? (
        <p className="success-banner" role="status">
          {notice}
        </p>
      ) : null}
      {resetDemo.isError ? (
        <p className="form-error" role="alert">
          {resetDemo.error.message}
        </p>
      ) : null}

      <div className="settings-grid">
        <section
          className="panel settings-section"
          aria-labelledby="provider-title"
        >
          <div className="settings-title">
            <span aria-hidden="true">✦</span>
            <div>
              <h2 id="provider-title">Narrative provider</h2>
              <p>Text and artifact generation</p>
            </div>
          </div>
          <ProviderStatus config={config.data} />
          <p className="settings-note">
            OpenAI mode is intentionally not implemented in this phase.
          </p>
        </section>

        <section
          className="panel settings-section"
          aria-labelledby="defaults-title"
        >
          <div className="settings-title">
            <span aria-hidden="true">⌁</span>
            <div>
              <h2 id="defaults-title">Simulation defaults</h2>
              <p>Used when starting a new scenario</p>
            </div>
          </div>
          <label className="setting-row">
            <span>
              <strong>Default mode</strong>
              <small>Sets the initial tone in scenario creation</small>
            </span>
            <select
              value={defaultMode}
              onChange={(event) => {
                setDefaultMode(event.target.value);
                window.localStorage.setItem(
                  "multiverse-default-mode",
                  event.target.value,
                );
              }}
            >
              {config.data.simulation_modes.map((mode) => (
                <option key={mode} value={mode}>
                  {mode[0]?.toUpperCase()}
                  {mode.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label className="setting-row">
            <span>
              <strong>Planning horizon</strong>
              <small>Universes still advance one year at a time</small>
            </span>
            <select
              value={defaultHorizon}
              onChange={(event) => {
                const value = Number(event.target.value);
                setDefaultHorizon(value);
                window.localStorage.setItem(
                  "multiverse-default-horizon",
                  String(value),
                );
              }}
            >
              {[3, 5, 7, 10].map((year) => (
                <option key={year} value={year}>
                  {year} years
                </option>
              ))}
            </select>
          </label>
        </section>

        <section
          className="panel settings-section"
          aria-labelledby="accessibility-title"
        >
          <div className="settings-title">
            <span aria-hidden="true">◎</span>
            <div>
              <h2 id="accessibility-title">Accessibility</h2>
              <p>Visual comfort and movement</p>
            </div>
          </div>
          <label className="setting-row">
            <span>
              <strong>Reduced motion</strong>
              <small>Stops decorative motion and shortens transitions</small>
            </span>
            <input
              className="toggle"
              type="checkbox"
              checked={reducedMotion}
              onChange={(event) => setReducedMotion(event.target.checked)}
            />
          </label>
        </section>

        <section
          className="panel settings-section danger-section"
          aria-labelledby="data-title"
        >
          <div className="settings-title">
            <span aria-hidden="true">↺</span>
            <div>
              <h2 id="data-title">Demo data</h2>
              <p>Restore the seeded experience</p>
            </div>
          </div>
          <p>
            Removes generated years, events, choices, artifacts, and chats from
            all three demo universes. The demo profile and scenario remain.
          </p>
          <button
            className="button button-danger"
            type="button"
            disabled={resetDemo.isPending}
            onClick={() => {
              if (
                window.confirm(
                  "Reset all three demo universes? Generated progress will be removed.",
                )
              )
                resetDemo.mutate();
            }}
          >
            {resetDemo.isPending ? "Resetting demo…" : "Reset demo database"}
          </button>
        </section>
      </div>

      <section className="panel about-panel" aria-labelledby="about-title">
        <div>
          <p className="eyebrow">About</p>
          <h2 id="about-title">{config.data.app_name}</h2>
          <span>Version {config.data.app_version}</span>
        </div>
        <p>{config.data.fictional_simulation_disclaimer}</p>
      </section>
    </section>
  );
}
