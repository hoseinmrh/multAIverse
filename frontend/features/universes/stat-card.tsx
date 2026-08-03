export function StatisticCard({
  label,
  value,
  accent = "#7aa2ff",
  inverse = false,
}: {
  label: string;
  value: number;
  accent?: string;
  inverse?: boolean;
}) {
  const normalized = Math.max(0, Math.min(100, value));
  const tone = inverse && normalized >= 70 ? " stat-card-warning" : "";
  return (
    <article className={`stat-card${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{Math.round(value)}</strong>
      </div>
      <div
        className="stat-meter"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(normalized)}
      >
        <span style={{ width: `${normalized}%`, backgroundColor: accent }} />
      </div>
    </article>
  );
}
