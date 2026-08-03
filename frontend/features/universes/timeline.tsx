import type { Event, LifeStateSnapshot } from "@/lib/api/schemas";

export function Timeline({
  snapshots,
  events,
  accent = "#7aa2ff",
}: {
  snapshots: LifeStateSnapshot[];
  events: Event[];
  accent?: string;
}) {
  if (!snapshots.length && !events.length) {
    return <p className="empty-copy">No years have been recorded yet.</p>;
  }
  const years = Array.from(
    new Set([
      ...snapshots.map((snapshot) => snapshot.year),
      ...events.map((event) => event.year),
    ]),
  ).sort((a, b) => b - a);
  return (
    <ol className="timeline-list" aria-label="Universe timeline">
      {years.map((year) => {
        const snapshot = snapshots.find((item) => item.year === year);
        const yearlyEvents = events.filter((item) => item.year === year);
        return (
          <li key={year}>
            <div
              className="timeline-marker"
              style={{ borderColor: accent }}
              aria-hidden="true"
            />
            <div className="timeline-year">
              <strong>{year}</strong>
              {snapshot ? (
                <span>Age {snapshot.age}</span>
              ) : (
                <span>Awaiting choice</span>
              )}
            </div>
            <div className="timeline-content">
              {yearlyEvents.length ? (
                yearlyEvents.map((event) => (
                  <article key={event.id}>
                    <div className="timeline-event-meta">
                      <span>{event.category}</span>
                      <span>{event.importance}</span>
                      {event.status === "pending" ? (
                        <b>Decision waiting</b>
                      ) : null}
                    </div>
                    <h3>{event.title}</h3>
                    <p>{event.description}</p>
                  </article>
                ))
              ) : snapshot ? (
                <article>
                  <div className="timeline-event-meta">
                    <span>Opening state</span>
                  </div>
                  <h3>{snapshot.career_title}</h3>
                  <p>
                    {snapshot.location} · Happiness {snapshot.happiness} ·
                    Stress {snapshot.stress}
                  </p>
                </article>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
