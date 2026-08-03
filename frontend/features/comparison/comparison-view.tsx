"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/async-state";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queries";
import type { Comparison, UniverseComparison } from "@/lib/api/schemas";
import { universeAccent } from "@/lib/constants";

const statKeys = [
  ["career_level", "Career"],
  ["health", "Health"],
  ["relationships", "Relationships"],
  ["research_impact", "Research"],
  ["freedom", "Freedom"],
  ["happiness", "Happiness"],
] as const;

const currency = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function buildComparisonSummary(comparison: Comparison): string {
  if (!comparison.universes.length)
    return "No universe data is available to compare yet.";
  const years = comparison.universes.flatMap((universe) =>
    universe.history.map((point) => point.year),
  );
  const happiness = comparison.universes.map(
    (universe) => universe.current_stats.happiness,
  );
  const stress = comparison.universes.map(
    (universe) => universe.current_stats.stress,
  );
  return `Across ${comparison.universes.length} fictional paths through ${Math.max(...years) || comparison.scenario.created_at.slice(0, 4)}, current happiness spans ${Math.min(...happiness)}–${Math.max(...happiness)} and stress spans ${Math.min(...stress)}–${Math.max(...stress)}. Each path trades a different mix of wellbeing, autonomy, work, research, and financial resilience; the simulation does not declare a single best universe.`;
}

function historyData(
  universes: UniverseComparison[],
  key: "happiness" | "stress" | "net_worth_eur",
) {
  const years = Array.from(
    new Set(
      universes.flatMap((universe) =>
        universe.history.map((point) => point.year),
      ),
    ),
  ).sort();
  return years.map((year) => {
    const row: Record<string, string | number> = { year };
    for (const universe of universes) {
      const point = universe.history.find((item) => item.year === year);
      if (point) row[universe.universe.id] = point[key];
    }
    return row;
  });
}

export function ComparisonView({ scenarioId }: { scenarioId: string }) {
  const comparison = useQuery({
    queryKey: queryKeys.comparison(scenarioId),
    queryFn: () => api.comparison(scenarioId),
  });
  if (comparison.isPending)
    return <LoadingState label="Aligning the universes…" />;
  if (comparison.isError)
    return (
      <ErrorState
        error={comparison.error}
        onRetry={() => void comparison.refetch()}
      />
    );
  if (!comparison.data.universes.length)
    return (
      <EmptyState
        title="Nothing to compare"
        message="Generate universes before opening comparison."
      />
    );

  const universes = comparison.data.universes;
  const radarData = statKeys.map(([key, label]) => {
    const row: Record<string, string | number> = { stat: label };
    universes.forEach((universe) => {
      row[universe.universe.id] = universe.current_stats[key];
    });
    return row;
  });
  const happinessData = historyData(universes, "happiness");
  const stressData = historyData(universes, "stress");
  const worthData = historyData(universes, "net_worth_eur");

  return (
    <section className="comparison-page" aria-labelledby="comparison-title">
      <header className="page-heading comparison-heading">
        <div>
          <Link className="back-link" href={`/multiverse/${scenarioId}`}>
            ← Multiverse map
          </Link>
          <p className="eyebrow">Cross-universe analysis</p>
          <h1 id="comparison-title">No single path tells the whole story.</h1>
          <p>{comparison.data.scenario.decision_question}</p>
        </div>
      </header>

      <div className="comparison-universe-strip">
        {universes.map((item, index) => {
          const accent = universeAccent(item.universe.visual_theme, index);
          return (
            <Link
              key={item.universe.id}
              href={`/universe/${item.universe.id}?scenario=${scenarioId}`}
              style={{ "--universe-accent": accent } as React.CSSProperties}
            >
              <span>
                {item.universe.current_year} · {item.location}
              </span>
              <strong>{item.universe.name}</strong>
              <small>{item.career_summary}</small>
            </Link>
          );
        })}
      </div>

      <div className="comparison-chart-grid">
        <section className="panel chart-panel" aria-labelledby="radar-title">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Current state</p>
              <h2 id="radar-title">Life balance</h2>
            </div>
          </div>
          <div className="chart-box" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} outerRadius="72%">
                <PolarGrid stroke="#34405f" />
                <PolarAngleAxis
                  dataKey="stat"
                  tick={{ fill: "#aeb9d4", fontSize: 12 }}
                />
                {universes.map((universe, index) => (
                  <Radar
                    key={universe.universe.id}
                    name={universe.universe.name}
                    dataKey={universe.universe.id}
                    stroke={universeAccent(
                      universe.universe.visual_theme,
                      index,
                    )}
                    fill={universeAccent(universe.universe.visual_theme, index)}
                    fillOpacity={0.08}
                    strokeWidth={2}
                  />
                ))}
                <Legend />
                <Tooltip
                  contentStyle={{
                    background: "#11172a",
                    border: "1px solid #2b3652",
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <table className="sr-only">
            <caption>Current statistic comparison</caption>
            <thead>
              <tr>
                <th>Statistic</th>
                {universes.map((item) => (
                  <th key={item.universe.id}>{item.universe.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {statKeys.map(([key, label]) => (
                <tr key={key}>
                  <th>{label}</th>
                  {universes.map((item) => (
                    <td key={item.universe.id}>{item.current_stats[key]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <HistoryChart
          title="Happiness over time"
          metric="happiness"
          data={happinessData}
          universes={universes}
        />
        <HistoryChart
          title="Stress over time"
          metric="stress"
          data={stressData}
          universes={universes}
        />
        <HistoryChart
          title="Net worth history"
          metric="net worth"
          data={worthData}
          universes={universes}
          currencyValues
        />
      </div>

      <section className="comparison-paths" aria-labelledby="paths-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">The shape of each life</p>
            <h2 id="paths-title">Paths, choices, and consequences</h2>
          </div>
        </div>
        <div>
          {universes.map((item, index) => (
            <article
              key={item.universe.id}
              className="panel path-card"
              style={
                {
                  "--universe-accent": universeAccent(
                    item.universe.visual_theme,
                    index,
                  ),
                } as React.CSSProperties
              }
            >
              <span className="path-number">0{index + 1}</span>
              <h3>{item.universe.name}</h3>
              <p>{item.career_summary}</p>
              <dl>
                <div>
                  <dt>Income</dt>
                  <dd>
                    {currency.format(
                      item.financial_position.monthly_income_eur,
                    )}
                    /mo
                  </dd>
                </div>
                <div>
                  <dt>Net worth</dt>
                  <dd>
                    {currency.format(item.financial_position.net_worth_eur)}
                  </dd>
                </div>
              </dl>
              <List
                title="Key decisions"
                values={item.key_decisions}
                empty="No decisions resolved yet."
              />
              <List
                title="Achievements"
                values={item.major_achievements}
                empty="Still unwritten."
              />
              <List
                title="Regrets"
                values={item.major_regrets}
                empty="No recorded regrets."
              />
            </article>
          ))}
        </div>
      </section>

      <section
        className="panel written-comparison"
        aria-labelledby="written-title"
      >
        <p className="eyebrow">Reading the divergence</p>
        <h2 id="written-title">A comparison, not a verdict</h2>
        <p>{buildComparisonSummary(comparison.data)}</p>
      </section>
    </section>
  );
}

function HistoryChart({
  title,
  metric,
  data,
  universes,
  currencyValues = false,
}: {
  title: string;
  metric: string;
  data: Array<Record<string, string | number>>;
  universes: UniverseComparison[];
  currencyValues?: boolean;
}) {
  return (
    <section className="panel chart-panel" aria-label={title}>
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Timeline</p>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="chart-box" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ left: 6, right: 18, top: 8, bottom: 4 }}
          >
            <CartesianGrid stroke="#28324b" strokeDasharray="3 6" />
            <XAxis dataKey="year" stroke="#75819f" />
            <YAxis
              stroke="#75819f"
              tickFormatter={(value: number) =>
                currencyValues ? currency.format(value) : String(value)
              }
            />
            <Tooltip
              contentStyle={{
                background: "#11172a",
                border: "1px solid #2b3652",
              }}
              formatter={(value) =>
                currencyValues && typeof value === "number"
                  ? currency.format(value)
                  : value
              }
            />
            <Legend />
            {universes.map((universe, index) => (
              <Line
                key={universe.universe.id}
                name={universe.universe.name}
                type="monotone"
                dataKey={universe.universe.id}
                stroke={universeAccent(universe.universe.visual_theme, index)}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th>Year</th>
            {universes.map((item) => (
              <th key={item.universe.id}>{item.universe.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={String(row.year)}>
              <th>{row.year}</th>
              {universes.map((item) => (
                <td key={item.universe.id}>
                  {row[item.universe.id] ?? "—"}{" "}
                  {metric === "net worth" ? "EUR" : ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function List({
  title,
  values,
  empty,
}: {
  title: string;
  values: string[];
  empty: string;
}) {
  return (
    <div className="comparison-list">
      <h4>{title}</h4>
      {values.length ? (
        <ul>
          {values.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      ) : (
        <p>{empty}</p>
      )}
    </div>
  );
}
