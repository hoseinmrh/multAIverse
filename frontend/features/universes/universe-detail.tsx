"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { ErrorState, LoadingState } from "@/components/ui/async-state";
import {
  ArtifactCard,
  ArtifactViewer,
} from "@/features/artifacts/artifact-card";
import { EventDecisionModal } from "@/features/universes/event-decision-modal";
import { StatisticCard } from "@/features/universes/stat-card";
import { Timeline } from "@/features/universes/timeline";
import { api } from "@/lib/api/client";
import { useRefreshUniverse, useUniverseBundle } from "@/lib/api/queries";
import type { Artifact, EventDetail } from "@/lib/api/schemas";
import { universeAccent } from "@/lib/constants";

const currency = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

export function UniverseDetail({
  universeId,
  scenarioId: scenarioIdFromUrl,
}: {
  universeId: string;
  scenarioId: string;
}) {
  const [stateQuery, timelineQuery, eventsQuery, artifactsQuery] =
    useUniverseBundle(universeId);
  const scenarioId = stateQuery.data?.universe.scenario_id ?? scenarioIdFromUrl;
  const refresh = useRefreshUniverse(universeId, scenarioId);
  const [openedArtifact, setOpenedArtifact] = useState<Artifact | null>(null);
  const [decision, setDecision] = useState<EventDetail | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const repairAttempted = useRef(false);

  const pendingEvent = eventsQuery.data?.items.find(
    (event) => event.status === "pending",
  );
  const pendingEventId = pendingEvent?.id;
  const customPathFlags = new Set([
    "career_path",
    "education_path",
    "creator_path",
    "independent_path",
  ]);
  const isLegacyCustomEvent = Boolean(
    pendingEvent?.narrative_key &&
    ["industry-", "research-", "startup-"].some((prefix) =>
      pendingEvent.narrative_key?.startsWith(prefix),
    ) &&
    stateQuery.data?.state.active_flags.some((flag) =>
      customPathFlags.has(flag),
    ),
  );
  const prepareScenario = useMutation({
    mutationFn: () => api.generateUniverses(scenarioId),
    onSuccess: async () => {
      setDecision(null);
      await refresh();
      setNotice("This decision was refreshed for the current story.");
    },
  });
  const prepareScenarioMutation = prepareScenario.mutate;

  useEffect(() => {
    if (!isLegacyCustomEvent || !scenarioId || repairAttempted.current) return;
    repairAttempted.current = true;
    prepareScenarioMutation();
  }, [isLegacyCustomEvent, prepareScenarioMutation, scenarioId]);

  const pendingDecision = useQuery({
    queryKey: ["event", pendingEventId],
    queryFn: () => api.event(pendingEventId ?? ""),
    enabled:
      Boolean(pendingEventId) &&
      (!isLegacyCustomEvent || prepareScenario.isError),
  });

  const advance = useMutation({
    mutationFn: () => api.advance(universeId),
    onSuccess: async (result) => {
      await refresh();
      if (result.blocked && result.event) {
        setDecision(result.event);
        setNotice(null);
      } else {
        setNotice(
          result.summary?.headline ?? `Advanced to ${result.target_year}.`,
        );
      }
    },
  });

  const selectChoice = useMutation({
    mutationFn: ({
      eventId,
      choiceId,
    }: {
      eventId: string;
      choiceId: string;
    }) => api.selectChoice(eventId, choiceId),
    onSuccess: async (result) => {
      setDecision(null);
      await refresh();
      setNotice(
        result.summary?.headline ??
          `The ${result.target_year} timeline is now resolved.`,
      );
    },
  });

  const reset = useMutation({
    mutationFn: () => api.resetUniverse(universeId),
    onSuccess: async () => {
      setDecision(null);
      setNotice("This universe returned to its 2026 starting state.");
      await refresh();
    },
  });

  const majorAchievements = useMemo(
    () =>
      eventsQuery.data?.items.filter(
        (event) =>
          event.status === "resolved" && event.importance !== "routine",
      ) ?? [],
    [eventsQuery.data?.items],
  );

  const firstError = [
    stateQuery,
    timelineQuery,
    eventsQuery,
    artifactsQuery,
  ].find((query) => query.isError);
  if (
    [stateQuery, timelineQuery, eventsQuery, artifactsQuery].some(
      (query) => query.isPending,
    )
  ) {
    return <LoadingState label="Loading this universe…" />;
  }
  if (firstError) {
    return (
      <ErrorState
        error={firstError.error}
        onRetry={() => {
          void stateQuery.refetch();
          void timelineQuery.refetch();
          void eventsQuery.refetch();
          void artifactsQuery.refetch();
        }}
      />
    );
  }
  if (
    !stateQuery.data ||
    !timelineQuery.data ||
    !eventsQuery.data ||
    !artifactsQuery.data
  ) {
    return null;
  }

  const { universe, state } = stateQuery.data;
  const accent = universeAccent(universe.visual_theme);
  const activeDecision =
    isLegacyCustomEvent && !prepareScenario.isError
      ? null
      : (decision ?? pendingDecision.data ?? null);
  const mutationError =
    advance.error ?? selectChoice.error ?? reset.error ?? prepareScenario.error;
  const statValues = [
    ["Happiness", state.happiness, false],
    ["Health", state.health, false],
    ["Relationships", state.relationships, false],
    ["Career", state.career_level, false],
    ["Research impact", state.research_impact, false],
    ["Freedom", state.freedom, false],
    ["Reputation", state.reputation, false],
    ["Stress", state.stress, true],
  ] as const;

  return (
    <div
      className="universe-page"
      style={{ "--universe-accent": accent } as React.CSSProperties}
    >
      <header className="universe-hero panel">
        <div className="universe-identity">
          <Link href={`/multiverse/${scenarioId}`} className="back-link">
            ← Multiverse map
          </Link>
          <p className="eyebrow">{universe.subtitle}</p>
          <h1>{universe.name}</h1>
          <p>{universe.premise}</p>
        </div>
        <dl className="universe-now">
          <div>
            <dt>Year</dt>
            <dd>{state.year}</dd>
          </div>
          <div>
            <dt>Age</dt>
            <dd>{state.age}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>{state.location}</dd>
          </div>
          <div>
            <dt>Current role</dt>
            <dd>{state.career_title}</dd>
          </div>
        </dl>
      </header>

      {notice ? (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="success-banner"
          role="status"
        >
          {notice}
        </motion.p>
      ) : null}
      {mutationError ? (
        <p className="form-error" role="alert">
          {mutationError.message}
        </p>
      ) : null}

      <section className="universe-actionbar" aria-label="Universe actions">
        <button
          className="button button-primary"
          type="button"
          disabled={
            advance.isPending ||
            universe.status === "blocked" ||
            Boolean(pendingEventId)
          }
          onClick={() => advance.mutate()}
        >
          {advance.isPending
            ? "Simulating year…"
            : universe.status === "blocked"
              ? "Decision required"
              : `Advance to ${state.year + 1}`}
        </button>
        <Link
          className="button button-secondary"
          href={`/future-self/${universeId}?scenario=${scenarioId}`}
        >
          Talk to future self
        </Link>
        <button
          className="button button-ghost"
          type="button"
          disabled
          title="Historical forking needs a backend API"
        >
          Fork from this point
        </button>
        <button
          className="button button-danger"
          type="button"
          disabled={reset.isPending}
          onClick={() => {
            if (
              window.confirm(
                "Reset this universe to 2026? Its later timeline will be removed.",
              )
            ) {
              reset.mutate();
            }
          }}
        >
          {reset.isPending ? "Resetting…" : "Reset universe"}
        </button>
      </section>

      <section aria-labelledby="stats-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Life state</p>
            <h2 id="stats-title">Statistics</h2>
          </div>
          <div className="finance-summary">
            <div>
              <span>Monthly income</span>
              <strong>{currency.format(state.monthly_income_eur)}</strong>
            </div>
            <div>
              <span>Net worth</span>
              <strong>{currency.format(state.net_worth_eur)}</strong>
            </div>
          </div>
        </div>
        <div className="stats-grid">
          {statValues.map(([label, value, inverse]) => (
            <StatisticCard
              key={label}
              label={label}
              value={value}
              accent={accent}
              inverse={inverse}
            />
          ))}
        </div>
      </section>

      <div className="universe-columns">
        <section
          className="panel timeline-panel"
          aria-labelledby="timeline-title"
        >
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Immutable history</p>
              <h2 id="timeline-title">Timeline</h2>
            </div>
            <span>{timelineQuery.data.pagination.total} snapshots</span>
          </div>
          <Timeline
            snapshots={timelineQuery.data.items}
            events={eventsQuery.data.items}
            accent={accent}
          />
        </section>
        <aside className="universe-sidebar">
          <section className="panel" aria-labelledby="achievements-title">
            <p className="eyebrow">Turning points</p>
            <h2 id="achievements-title">Major achievements</h2>
            {majorAchievements.length ? (
              <ul className="simple-list">
                {majorAchievements
                  .slice(-5)
                  .reverse()
                  .map((event) => (
                    <li key={event.id}>
                      {event.title}
                      <span>{event.year}</span>
                    </li>
                  ))}
              </ul>
            ) : (
              <p className="empty-copy">
                Advance the timeline to reveal achievements.
              </p>
            )}
          </section>
          <section className="panel" aria-labelledby="effects-title">
            <p className="eyebrow">Live context</p>
            <h2 id="effects-title">Active effects</h2>
            {state.active_flags.length ? (
              <div className="flag-list">
                {state.active_flags.map((flag) => (
                  <span key={flag}>{flag.replaceAll("_", " ")}</span>
                ))}
              </div>
            ) : (
              <p className="empty-copy">No active flags.</p>
            )}
          </section>
        </aside>
      </div>

      <section aria-labelledby="artifacts-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Evidence from this reality</p>
            <h2 id="artifacts-title">Artifacts</h2>
          </div>
          <span>{artifactsQuery.data.pagination.total} collected</span>
        </div>
        {artifactsQuery.data.items.length ? (
          <div className="artifact-grid">
            {artifactsQuery.data.items
              .slice()
              .reverse()
              .map((artifact) => (
                <ArtifactCard
                  key={artifact.id}
                  artifact={artifact}
                  onOpen={() => setOpenedArtifact(artifact)}
                />
              ))}
          </div>
        ) : (
          <div className="panel empty-copy">
            The first resolved year will create a fictional artifact.
          </div>
        )}
      </section>

      {activeDecision ? (
        <EventDecisionModal
          detail={activeDecision}
          isSubmitting={selectChoice.isPending}
          onConfirm={(choiceId) =>
            selectChoice.mutate({ eventId: activeDecision.event.id, choiceId })
          }
        />
      ) : null}
      {openedArtifact ? (
        <ArtifactViewer
          artifact={openedArtifact}
          onClose={() => setOpenedArtifact(null)}
        />
      ) : null}
    </div>
  );
}
