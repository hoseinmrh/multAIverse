"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { useCreateProfile } from "@/lib/api/queries";
import { profileCreateSchema, type ProfileCreate } from "@/lib/api/schemas";

const steps = [
  "Identity",
  "Situation",
  "Goals",
  "Strengths",
  "Constraints",
  "Statistics",
  "Review",
] as const;

const defaultStats = {
  career_level: 45,
  health: 70,
  relationships: 65,
  research_impact: 35,
  reputation: 40,
  freedom: 55,
  stress: 50,
  happiness: 68,
  discipline: 65,
  creativity: 65,
  chaos: 30,
};

const initialProfile: ProfileCreate = {
  name: "",
  birth_year: 1996,
  starting_year: 2026,
  starting_age: 30,
  location: "",
  occupation: "",
  education: "",
  biography: "",
  strengths: [],
  weaknesses: [],
  interests: [],
  goals: [],
  constraints: [],
  starting_stats: defaultStats,
};

const listValue = (values: string[]) => values.join(", ");
const parseList = (value: string) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

export function ProfileForm() {
  const router = useRouter();
  const createProfile = useCreateProfile();
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState<ProfileCreate>(initialProfile);
  const [error, setError] = useState<string | null>(null);

  const progress = `${step + 1} of ${steps.length}`;
  const currentErrors = useMemo(() => {
    const parsed = profileCreateSchema.safeParse(profile);
    return parsed.success
      ? []
      : parsed.error.issues.map((issue) => issue.message);
  }, [profile]);

  const setField = <Key extends keyof ProfileCreate>(
    key: Key,
    value: ProfileCreate[Key],
  ) => setProfile((current) => ({ ...current, [key]: value }));

  const updateYear = (key: "birth_year" | "starting_year", value: number) => {
    setProfile((current) => {
      const next = { ...current, [key]: value };
      return {
        ...next,
        starting_age: Math.max(0, next.starting_year - next.birth_year),
      };
    });
  };

  const next = () => {
    setError(null);
    if (step === 0 && !profile.name.trim()) {
      setError("Tell us what to call this fictional protagonist.");
      return;
    }
    if (
      step === 1 &&
      (!profile.location.trim() ||
        !profile.occupation.trim() ||
        !profile.education.trim())
    ) {
      setError("Location, current role, and education are required.");
      return;
    }
    setStep((current) => Math.min(steps.length - 1, current + 1));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const result = profileCreateSchema.safeParse(profile);
    if (!result.success) {
      setError(
        result.error.issues[0]?.message ?? "Review the profile details.",
      );
      return;
    }
    try {
      const created = await createProfile.mutateAsync(result.data);
      router.push(`/scenario?profile=${created.id}`);
    } catch (mutationError) {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : "The profile could not be saved.",
      );
    }
  };

  return (
    <form className="onboarding-grid" onSubmit={submit} noValidate>
      <aside className="onboarding-steps" aria-label="Profile setup progress">
        <p className="eyebrow">Profile onboarding</p>
        <h1>Tell us where this story begins.</h1>
        <ol>
          {steps.map((label, index) => (
            <li key={label} aria-current={index === step ? "step" : undefined}>
              <span>{index + 1}</span>
              {label}
            </li>
          ))}
        </ol>
      </aside>

      <section className="form-panel" aria-labelledby="form-step-title">
        <div className="form-progress">
          <span>{progress}</span>
          <div className="progress-track" aria-hidden="true">
            <div style={{ width: `${((step + 1) / steps.length) * 100}%` }} />
          </div>
        </div>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            className="form-step"
          >
            <h2 id="form-step-title">{steps[step]}</h2>
            {step === 0 ? (
              <div className="field-grid">
                <label className="field field-wide">
                  <span>Name</span>
                  <input
                    autoFocus
                    value={profile.name}
                    onChange={(event) => setField("name", event.target.value)}
                    placeholder="Your name"
                  />
                </label>
                <label className="field">
                  <span>Birth year</span>
                  <input
                    type="number"
                    min="1901"
                    value={profile.birth_year}
                    onChange={(event) =>
                      updateYear("birth_year", Number(event.target.value))
                    }
                  />
                </label>
                <label className="field">
                  <span>Story starts</span>
                  <input
                    type="number"
                    min="1901"
                    value={profile.starting_year}
                    onChange={(event) =>
                      updateYear("starting_year", Number(event.target.value))
                    }
                  />
                </label>
                <div className="computed-field">
                  <span>Starting age</span>
                  <strong>{profile.starting_age}</strong>
                </div>
              </div>
            ) : null}
            {step === 1 ? (
              <div className="field-grid">
                <label className="field">
                  <span>Current city</span>
                  <input
                    autoFocus
                    value={profile.location}
                    onChange={(event) =>
                      setField("location", event.target.value)
                    }
                    placeholder="Milan"
                  />
                </label>
                <label className="field">
                  <span>Current role</span>
                  <input
                    value={profile.occupation}
                    onChange={(event) =>
                      setField("occupation", event.target.value)
                    }
                    placeholder="Product designer"
                  />
                </label>
                <label className="field field-wide">
                  <span>Education</span>
                  <input
                    value={profile.education}
                    onChange={(event) =>
                      setField("education", event.target.value)
                    }
                    placeholder="MSc student, self-taught, or another path"
                  />
                </label>
                <label className="field field-wide">
                  <span>
                    Short biography <small>optional</small>
                  </span>
                  <textarea
                    value={profile.biography}
                    onChange={(event) =>
                      setField("biography", event.target.value)
                    }
                    placeholder="What context matters for the paths ahead?"
                  />
                </label>
              </div>
            ) : null}
            {step === 2 ? (
              <div className="field-grid">
                <ListField
                  autoFocus
                  label="Goals"
                  hint="Separate items with commas"
                  value={listValue(profile.goals)}
                  onChange={(value) => setField("goals", parseList(value))}
                />
                <ListField
                  label="Interests"
                  value={listValue(profile.interests)}
                  onChange={(value) => setField("interests", parseList(value))}
                />
              </div>
            ) : null}
            {step === 3 ? (
              <div className="field-grid">
                <ListField
                  autoFocus
                  label="Strengths"
                  hint="What gives you an edge?"
                  value={listValue(profile.strengths)}
                  onChange={(value) => setField("strengths", parseList(value))}
                />
                <ListField
                  label="Growth edges"
                  value={listValue(profile.weaknesses)}
                  onChange={(value) => setField("weaknesses", parseList(value))}
                />
              </div>
            ) : null}
            {step === 4 ? (
              <div className="field-grid">
                <ListField
                  autoFocus
                  label="Constraints"
                  hint="Time, money, commitments, geography, energy…"
                  value={listValue(profile.constraints)}
                  onChange={(value) =>
                    setField("constraints", parseList(value))
                  }
                />
                <p className="form-note">
                  Constraints make the simulation more interesting. They are
                  story inputs, not judgments.
                </p>
              </div>
            ) : null}
            {step === 5 ? (
              <div className="stat-sliders">
                {Object.entries(profile.starting_stats).map(([name, value]) => (
                  <label key={name}>
                    <span>{name.replaceAll("_", " ")}</span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={value}
                      onChange={(event) =>
                        setField("starting_stats", {
                          ...profile.starting_stats,
                          [name]: Number(event.target.value),
                        })
                      }
                    />
                    <output>{value}</output>
                  </label>
                ))}
              </div>
            ) : null}
            {step === 6 ? (
              <div className="review-card">
                <span className="review-monogram" aria-hidden="true">
                  {profile.name.slice(0, 1).toUpperCase() || "?"}
                </span>
                <div>
                  <p className="eyebrow">Protagonist</p>
                  <h3>{profile.name || "Unnamed protagonist"}</h3>
                  <p>
                    Age {profile.starting_age} in{" "}
                    {profile.location || "an unknown city"} ·{" "}
                    {profile.occupation || "role not set"}
                  </p>
                </div>
                <dl>
                  <div>
                    <dt>Goals</dt>
                    <dd>{profile.goals.join(", ") || "Open-ended"}</dd>
                  </div>
                  <div>
                    <dt>Strengths</dt>
                    <dd>
                      {profile.strengths.join(", ") || "To emerge through play"}
                    </dd>
                  </div>
                  <div>
                    <dt>Constraints</dt>
                    <dd>
                      {profile.constraints.join(", ") || "None specified"}
                    </dd>
                  </div>
                </dl>
                {currentErrors.length ? (
                  <p className="inline-warning">{currentErrors[0]}</p>
                ) : null}
              </div>
            ) : null}
          </motion.div>
        </AnimatePresence>

        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="form-actions">
          <button
            className="button button-ghost"
            type="button"
            disabled={step === 0}
            onClick={() => setStep((current) => Math.max(0, current - 1))}
          >
            Back
          </button>
          {step < steps.length - 1 ? (
            <button
              className="button button-primary"
              type="button"
              onClick={next}
            >
              Continue
            </button>
          ) : (
            <button
              className="button button-primary"
              type="submit"
              disabled={createProfile.isPending || currentErrors.length > 0}
            >
              {createProfile.isPending
                ? "Saving profile…"
                : "Choose a decision"}
            </button>
          )}
        </div>
      </section>
    </form>
  );
}

function ListField({
  label,
  hint,
  value,
  onChange,
  autoFocus = false,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
}) {
  return (
    <label className="field field-wide">
      <span>
        {label} {hint ? <small>{hint}</small> : null}
      </span>
      <textarea
        autoFocus={autoFocus}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={`${label} separated by commas`}
      />
    </label>
  );
}
