"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useCreateScenario } from "@/lib/api/queries";
import { scenarioCreateSchema, type SimulationMode } from "@/lib/api/schemas";

const modes: Array<{
  value: SimulationMode;
  label: string;
  description: string;
}> = [
  {
    value: "realistic",
    label: "Realistic",
    description: "Grounded progress and setbacks",
  },
  {
    value: "cinematic",
    label: "Cinematic",
    description: "Sharper reversals and turning points",
  },
  {
    value: "utopian",
    label: "Utopian",
    description: "Favorable, still coherent conditions",
  },
  {
    value: "dark",
    label: "Dark",
    description: "Pressure, trade-offs, and recovery",
  },
  {
    value: "chaos",
    label: "Chaos",
    description: "Improbable but consistent detours",
  },
];

export function ScenarioForm({ profileId }: { profileId: string }) {
  const router = useRouter();
  const createScenario = useCreateScenario();
  const [title, setTitle] = useState("My next chapter");
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [mode, setMode] = useState<SimulationMode>("realistic");
  const [horizon, setHorizon] = useState(5);
  const [directions, setDirections] = useState(["", "", ""]);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const customDirections = directions.filter((direction) => direction.trim());
    const description = [
      context.trim(),
      `Planning horizon: ${horizon} years.`,
      customDirections.length
        ? `Optional branch directions: ${customDirections.join(" | ")}.`
        : "",
    ]
      .filter(Boolean)
      .join("\n\n");
    const candidate = {
      profile_id: profileId,
      title,
      decision_question: question,
      description,
      number_of_universes: 3 as const,
      simulation_mode: mode,
      seed: Date.now() % 2_147_483_647,
    };
    const parsed = scenarioCreateSchema.safeParse(candidate);
    if (!parsed.success) {
      setError(
        parsed.error.issues[0]?.message ?? "Review the scenario details.",
      );
      return;
    }
    try {
      const scenario = await createScenario.mutateAsync(parsed.data);
      router.push(`/multiverse/${scenario.id}`);
    } catch (mutationError) {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : "This scenario could not be created.",
      );
    }
  };

  return (
    <div className="scenario-layout">
      <header className="page-heading">
        <p className="eyebrow">New scenario</p>
        <h1>What question keeps following you?</h1>
        <p>
          The mock narrative provider will turn one decision into three
          server-backed, deterministic starting realities.
        </p>
      </header>
      <form className="scenario-form panel" onSubmit={submit} noValidate>
        <label className="field">
          <span>Scenario title</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Decision question</span>
          <textarea
            autoFocus
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Should I remain in industry, pursue a PhD, or launch my startup?"
          />
        </label>
        <label className="field">
          <span>
            Context <small>optional</small>
          </span>
          <textarea
            value={context}
            onChange={(event) => setContext(event.target.value)}
            placeholder="What makes this decision difficult right now?"
          />
        </label>

        <fieldset className="mode-picker">
          <legend>Simulation mode</legend>
          <div>
            {modes.map((item) => (
              <label
                key={item.value}
                className={mode === item.value ? "selected" : ""}
              >
                <input
                  type="radio"
                  name="mode"
                  value={item.value}
                  checked={mode === item.value}
                  onChange={() => setMode(item.value)}
                />
                <strong>{item.label}</strong>
                <span>{item.description}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <label className="horizon-field">
          <span>
            Time horizon <strong>{horizon} years</strong>
          </span>
          <input
            type="range"
            min="3"
            max="10"
            value={horizon}
            onChange={(event) => setHorizon(Number(event.target.value))}
          />
          <small>
            Years advance one at a time so every important choice remains yours.
          </small>
        </label>

        <fieldset className="branch-directions">
          <legend>Optional branch directions</legend>
          <p>Leave these blank to let the provider derive three directions.</p>
          <div>
            {directions.map((direction, index) => (
              <label key={index}>
                <span>Branch {String.fromCharCode(65 + index)}</span>
                <input
                  value={direction}
                  onChange={(event) =>
                    setDirections((current) =>
                      current.map((value, itemIndex) =>
                        itemIndex === index ? event.target.value : value,
                      ),
                    )
                  }
                  placeholder={
                    ["Stay in industry", "Pursue research", "Build a company"][
                      index
                    ]
                  }
                />
              </label>
            ))}
          </div>
        </fieldset>

        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <motion.button
          whileTap={{ scale: 0.98 }}
          className="button button-primary scenario-submit"
          type="submit"
          disabled={createScenario.isPending || !profileId}
        >
          {createScenario.isPending
            ? "Generating three universes…"
            : "Generate universes"}
        </motion.button>
      </form>
    </div>
  );
}
