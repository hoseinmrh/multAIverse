import { z } from "zod";

const jsonRecordSchema = z.record(z.string(), z.unknown());
// Universes created before browser-safe seed generation may contain signed
// 64-bit integers. JSON.parse rounds those values, but the seed is opaque in
// the frontend, so only integer shape—not safe-integer precision—is required.
const legacySeedSchema = z
  .number()
  .refine(Number.isInteger, "Expected an integer seed.");

export const simulationModeSchema = z.enum([
  "realistic",
  "cinematic",
  "utopian",
  "dark",
  "chaos",
]);

export const paginationSchema = z.object({
  offset: z.number().int().nonnegative(),
  limit: z.number().int().positive(),
  total: z.number().int().nonnegative(),
  has_more: z.boolean(),
});

export const publicConfigSchema = z.object({
  app_name: z.string(),
  app_version: z.string(),
  narrative_provider: z.enum(["mock", "openai"]),
  narrative_provider_status: z.object({
    active_provider: z.enum(["mock", "openai"]).nullable(),
    state: z.enum(["ready", "configured", "fallback", "unavailable"]),
    model: z.string().nullable(),
    fallback_enabled: z.boolean(),
    detail: z.string(),
  }),
  simulation_modes: z.array(simulationModeSchema),
  max_universe_branches: z.number().int().positive(),
  fictional_simulation_disclaimer: z.string(),
});

export const profileSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  birth_year: z.number().int(),
  starting_year: z.number().int(),
  starting_age: z.number().int(),
  location: z.string(),
  occupation: z.string(),
  education: z.string(),
  biography: z.string(),
  strengths: z.array(z.string()),
  weaknesses: z.array(z.string()),
  interests: z.array(z.string()),
  goals: z.array(z.string()),
  constraints: z.array(z.string()),
  starting_stats: z.record(z.string(), z.number()),
  created_at: z.string(),
  updated_at: z.string(),
});

export const profileCreateSchema = profileSchema
  .omit({ id: true, created_at: true, updated_at: true })
  .superRefine((value, context) => {
    if (value.starting_year < value.birth_year) {
      context.addIssue({
        code: "custom",
        path: ["starting_year"],
        message: "Starting year must be after the birth year.",
      });
    }
    if (value.starting_year - value.birth_year !== value.starting_age) {
      context.addIssue({
        code: "custom",
        path: ["starting_age"],
        message: "Age must match the starting and birth years.",
      });
    }
  });

export const scenarioSchema = z.object({
  id: z.string().uuid(),
  profile_id: z.string().uuid(),
  title: z.string(),
  decision_question: z.string(),
  description: z.string(),
  number_of_universes: z.number().int(),
  simulation_mode: simulationModeSchema,
  seed: z.number().int(),
  created_at: z.string(),
});

export const scenarioCreateSchema = scenarioSchema
  .omit({ id: true, created_at: true })
  .extend({
    title: z.string().trim().min(3, "Give this scenario a short title."),
    decision_question: z
      .string()
      .trim()
      .min(12, "Ask a specific life decision question."),
    description: z.string().trim().max(2_000),
    number_of_universes: z.literal(3),
  });

export const universeSchema = z.object({
  id: z.string().uuid(),
  scenario_id: z.string().uuid(),
  name: z.string(),
  slug: z.string(),
  subtitle: z.string(),
  premise: z.string(),
  visual_theme: jsonRecordSchema,
  starting_direction: z.string(),
  current_year: z.number().int(),
  current_age: z.number().int(),
  random_seed: legacySeedSchema,
  status: z.enum(["active", "blocked", "completed", "archived"]),
  created_at: z.string(),
  updated_at: z.string(),
});

export const snapshotSchema = z.object({
  id: z.string().uuid(),
  universe_id: z.string().uuid(),
  year: z.number().int(),
  age: z.number().int(),
  location: z.string(),
  career_title: z.string(),
  career_level: z.number(),
  monthly_income_eur: z.number(),
  net_worth_eur: z.number(),
  health: z.number(),
  relationships: z.number(),
  research_impact: z.number(),
  reputation: z.number(),
  freedom: z.number(),
  stress: z.number(),
  happiness: z.number(),
  discipline: z.number(),
  creativity: z.number(),
  chaos: z.number(),
  skills: jsonRecordSchema,
  active_flags: z.array(z.string()),
  created_at: z.string(),
});

export const eventSchema = z.object({
  id: z.string().uuid(),
  universe_id: z.string().uuid(),
  year: z.number().int(),
  narrative_key: z.string().nullable(),
  title: z.string(),
  description: z.string(),
  category: z.string(),
  importance: z.enum(["routine", "notable", "major"]),
  event_type: z.enum(["narrative", "decision", "milestone"]),
  status: z.enum(["pending", "resolved"]),
  is_generated: z.boolean(),
  source: z.string(),
  created_at: z.string(),
});

export const choiceSchema = z.object({
  id: z.string().uuid(),
  event_id: z.string().uuid(),
  label: z.string(),
  description: z.string(),
  immediate_effects: jsonRecordSchema,
  delayed_effects: z.array(z.unknown()),
  requirements: jsonRecordSchema,
  risk_level: z.enum(["low", "medium", "high"]),
  selected: z.boolean(),
  selected_at: z.string().nullable(),
});

export const artifactSchema = z.object({
  id: z.string().uuid(),
  universe_id: z.string().uuid(),
  event_id: z.string().uuid().nullable(),
  year: z.number().int(),
  artifact_type: z.string(),
  title: z.string(),
  content: jsonRecordSchema,
  metadata: jsonRecordSchema,
  created_at: z.string(),
});

export const eventDetailSchema = z.object({
  event: eventSchema,
  choices: z.array(choiceSchema),
});

export const advancementSchema = z.object({
  universe_id: z.string().uuid(),
  target_year: z.number().int(),
  blocked: z.boolean(),
  idempotent: z.boolean(),
  state: snapshotSchema.nullable().optional(),
  event: eventDetailSchema.nullable().optional(),
  summary: z
    .object({
      year: z.number().int(),
      headline: z.string(),
      overview: z.string(),
      key_developments: z.array(z.string()),
      defining_tradeoff: z.string(),
      closing_note: z.string(),
      narrative_tags: z.array(z.string()),
    })
    .nullable()
    .optional(),
  artifacts: z.array(artifactSchema).default([]),
});

export const scenarioDetailSchema = z.object({
  scenario: scenarioSchema,
  universes: z.array(universeSchema),
});

export const generationSchema = z.object({
  generated: z.boolean(),
  universes: z.array(universeSchema),
});

export const universeStateSchema = z.object({
  universe: universeSchema,
  state: snapshotSchema,
});

const comparisonStatsSchema = z.object({
  career_level: z.number(),
  health: z.number(),
  relationships: z.number(),
  research_impact: z.number(),
  reputation: z.number(),
  freedom: z.number(),
  stress: z.number(),
  happiness: z.number(),
  discipline: z.number(),
  creativity: z.number(),
  chaos: z.number(),
});

export const universeComparisonSchema = z.object({
  universe: universeSchema,
  current_stats: comparisonStatsSchema,
  financial_position: z.object({
    monthly_income_eur: z.number(),
    net_worth_eur: z.number(),
  }),
  location: z.string(),
  career_summary: z.string(),
  major_achievements: z.array(z.string()),
  major_regrets: z.array(z.string()),
  key_decisions: z.array(z.string()),
  history: z.array(
    z.object({
      year: z.number().int(),
      happiness: z.number(),
      stress: z.number(),
      net_worth_eur: z.number(),
    }),
  ),
  score_components: z.object({
    wellbeing: z.number(),
    sustainability: z.number(),
    career_momentum: z.number(),
    research_momentum: z.number(),
    financial_resilience: z.number(),
  }),
});

export const comparisonSchema = z.object({
  scenario: scenarioSchema,
  universes: z.array(universeComparisonSchema),
});

export const futureSelfIdentitySchema = z.object({
  name: z.string(),
  age: z.number().int(),
  location: z.string(),
  occupation: z.string(),
  universe: z.string(),
  key_achievement: z.string(),
  greatest_regret: z.string(),
  happiness: z.number(),
  stress: z.number(),
  personality_summary: z.string(),
  fictional_character: z.literal(true),
});

export const futureSelfConversationSchema = z.object({
  conversation: z.object({
    id: z.string().uuid(),
    universe_id: z.string().uuid(),
    title: z.string(),
    future_self_age: z.number().int(),
    personality_summary: z.string(),
    created_at: z.string(),
  }),
  identity: futureSelfIdentitySchema,
  messages: z.array(
    z.object({
      id: z.string().uuid(),
      conversation_id: z.string().uuid(),
      role: z.enum(["user", "future_self", "system"]),
      content: z.string(),
      state_snapshot_id: z.string().uuid().nullable(),
      created_at: z.string(),
    }),
  ),
  pagination: paginationSchema,
});

export const profilePageSchema = z.object({
  items: z.array(profileSchema),
  pagination: paginationSchema,
});
export const scenarioPageSchema = z.object({
  items: z.array(scenarioSchema),
  pagination: paginationSchema,
});
export const timelinePageSchema = z.object({
  items: z.array(snapshotSchema),
  pagination: paginationSchema,
});
export const eventPageSchema = z.object({
  items: z.array(eventSchema),
  pagination: paginationSchema,
});
export const artifactPageSchema = z.object({
  items: z.array(artifactSchema),
  pagination: paginationSchema,
});

export type PublicConfig = z.infer<typeof publicConfigSchema>;
export type Profile = z.infer<typeof profileSchema>;
export type ProfileCreate = z.infer<typeof profileCreateSchema>;
export type Scenario = z.infer<typeof scenarioSchema>;
export type ScenarioCreate = z.infer<typeof scenarioCreateSchema>;
export type SimulationMode = z.infer<typeof simulationModeSchema>;
export type Universe = z.infer<typeof universeSchema>;
export type LifeStateSnapshot = z.infer<typeof snapshotSchema>;
export type Event = z.infer<typeof eventSchema>;
export type Choice = z.infer<typeof choiceSchema>;
export type EventDetail = z.infer<typeof eventDetailSchema>;
export type Advancement = z.infer<typeof advancementSchema>;
export type Artifact = z.infer<typeof artifactSchema>;
export type UniverseComparison = z.infer<typeof universeComparisonSchema>;
export type Comparison = z.infer<typeof comparisonSchema>;
export type FutureSelfConversation = z.infer<
  typeof futureSelfConversationSchema
>;
