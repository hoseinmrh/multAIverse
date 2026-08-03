import { describe, expect, it } from "vitest";

import { profileCreateSchema, scenarioCreateSchema } from "@/lib/api/schemas";

describe("frontend validation", () => {
  it("rejects a profile with inconsistent age and required identity gaps", () => {
    const result = profileCreateSchema.safeParse({
      name: "",
      birth_year: 2000,
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
      starting_stats: {},
    });
    expect(result.success).toBe(false);
    if (!result.success)
      expect(
        result.error.issues.some((issue) => issue.path[0] === "starting_age"),
      ).toBe(true);
  });

  it("accepts exactly three branches and rejects a vague decision", () => {
    const base = {
      profile_id: "10000000-0000-4000-8000-000000000001",
      title: "Next chapter",
      decision_question: "What next?",
      description: "",
      number_of_universes: 3 as const,
      simulation_mode: "realistic" as const,
      seed: 42,
    };
    expect(scenarioCreateSchema.safeParse(base).success).toBe(false);
    expect(
      scenarioCreateSchema.safeParse({
        ...base,
        decision_question: "Should I pursue research or build a company?",
      }).success,
    ).toBe(true);
  });
});
