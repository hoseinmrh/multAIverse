"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/async-state";
import { useProfiles, useScenarios } from "@/lib/api/queries";
import { api } from "@/lib/api/client";

function displayDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function OpenScenarioButton({ scenarioId }: { scenarioId: string }) {
  const router = useRouter();
  const [isOpening, setIsOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const open = async () => {
    setIsOpening(true);
    setError(null);
    try {
      await api.generateUniverses(scenarioId);
      router.push(`/multiverse/${scenarioId}`);
    } catch (openError) {
      setError(
        openError instanceof Error
          ? openError.message
          : "This story could not be opened.",
      );
      setIsOpening(false);
    }
  };

  return (
    <div className="story-open-action">
      <button
        className="button button-secondary"
        type="button"
        disabled={isOpening}
        onClick={() => void open()}
      >
        {isOpening ? "Preparing universes…" : "Open three universes"}
      </button>
      {error ? (
        <small className="form-error" role="alert">
          {error}
        </small>
      ) : null}
    </div>
  );
}

export function StoryLibrary() {
  const profiles = useProfiles();
  const scenarios = useScenarios();

  if (profiles.isPending || scenarios.isPending)
    return <LoadingState label="Loading saved stories…" />;
  if (profiles.isError || scenarios.isError) {
    const failedQuery = profiles.isError ? profiles : scenarios;
    return (
      <ErrorState
        error={failedQuery.error}
        onRetry={() => void failedQuery.refetch()}
      />
    );
  }

  if (!profiles.data.items.length)
    return (
      <EmptyState
        title="No saved stories yet"
        message="Create a person and their first decision to begin."
      />
    );

  return (
    <section className="story-library" aria-labelledby="stories-title">
      <header className="page-heading story-library-heading">
        <div>
          <p className="eyebrow">Local story library</p>
          <h1 id="stories-title">Saved stories</h1>
          <p>
            Open any person&apos;s scenario, or start another decision from an
            existing profile.
          </p>
        </div>
        <Link className="button button-primary" href="/onboarding">
          New person
        </Link>
      </header>

      <div className="story-profile-list">
        {profiles.data.items.map((profile) => {
          const profileScenarios = scenarios.data.items.filter(
            (scenario) => scenario.profile_id === profile.id,
          );
          return (
            <article className="panel story-profile-card" key={profile.id}>
              <header>
                <div className="story-profile-avatar" aria-hidden="true">
                  {profile.name.slice(0, 1).toUpperCase() || "?"}
                </div>
                <div>
                  <h2>{profile.name}</h2>
                  <p>
                    {profile.occupation} · {profile.location}
                  </p>
                  <small>
                    Profile created {displayDate(profile.created_at)}
                  </small>
                </div>
                <Link
                  className="button button-ghost"
                  href={`/scenario?profile=${profile.id}`}
                >
                  New scenario
                </Link>
              </header>

              {profileScenarios.length ? (
                <div className="story-scenario-list">
                  {profileScenarios.map((scenario) => (
                    <section key={scenario.id} className="story-scenario-row">
                      <div>
                        <span>{scenario.simulation_mode} simulation</span>
                        <h3>{scenario.title}</h3>
                        <p>{scenario.decision_question}</p>
                      </div>
                      <OpenScenarioButton scenarioId={scenario.id} />
                    </section>
                  ))}
                </div>
              ) : (
                <div className="story-profile-empty">
                  <p>No scenario has been created for this person yet.</p>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
