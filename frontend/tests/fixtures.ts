import type {
  Artifact,
  Comparison,
  Event,
  EventDetail,
  FutureSelfConversation,
  LifeStateSnapshot,
  Universe,
} from "@/lib/api/schemas";

export const universe: Universe = {
  id: "30000000-0000-4000-8000-000000000001",
  scenario_id: "20000000-0000-4000-8000-000000000001",
  name: "Applied AI Leader",
  slug: "applied-ai-leader",
  subtitle: "Responsible systems leadership",
  premise: "A fictional industry path.",
  visual_theme: { accent: "#3B82F6", motif: "structured-grid" },
  starting_direction: "Build applied AI systems.",
  current_year: 2027,
  current_age: 26,
  random_seed: 202601,
  status: "active",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2027-01-01T00:00:00Z",
};

export const snapshot: LifeStateSnapshot = {
  id: "40000000-0000-4000-8000-000000000001",
  universe_id: universe.id,
  year: 2026,
  age: 25,
  location: "Milan",
  career_title: "AI Research Engineer",
  career_level: 48,
  monthly_income_eur: 3200,
  net_worth_eur: 14000,
  health: 77,
  relationships: 63,
  research_impact: 47,
  reputation: 42,
  freedom: 50,
  stress: 60,
  happiness: 69,
  discipline: 84,
  creativity: 79,
  chaos: 26,
  skills: { applied_ai: 72 },
  active_flags: ["industry_path"],
  created_at: "2026-01-01T00:00:00Z",
};

export const event: Event = {
  id: "50000000-0000-4000-8000-000000000001",
  universe_id: universe.id,
  year: 2027,
  narrative_key: "leadership-offer",
  title: "The leadership offer",
  description: "A high-visibility role creates a difficult trade-off.",
  category: "career",
  importance: "major",
  event_type: "decision",
  status: "pending",
  is_generated: true,
  source: "mock",
  created_at: "2027-01-01T00:00:00Z",
};

export const eventDetail: EventDetail = {
  event,
  choices: [
    {
      id: "60000000-0000-4000-8000-000000000001",
      event_id: event.id,
      label: "Take the ambitious route",
      description: "Accept greater visibility and responsibility.",
      immediate_effects: { stats: { career_level: 7, stress: 6 } },
      delayed_effects: [{ trigger_after_years: 2 }],
      requirements: {},
      risk_level: "high",
      selected: false,
      selected_at: null,
    },
    {
      id: "60000000-0000-4000-8000-000000000002",
      event_id: event.id,
      label: "Choose the measured route",
      description: "Protect health and room to adapt.",
      immediate_effects: { stats: { freedom: 4, stress: -3 } },
      delayed_effects: [],
      requirements: {},
      risk_level: "low",
      selected: false,
      selected_at: null,
    },
  ],
};

export function artifact(
  type: string,
  content: Record<string, unknown>,
): Artifact {
  return {
    id: "70000000-0000-4000-8000-000000000001",
    universe_id: universe.id,
    event_id: event.id,
    year: 2027,
    artifact_type: type,
    title: "A fictional artifact",
    content,
    metadata: { is_fictional: true },
    created_at: "2027-01-01T00:00:00Z",
  };
}

export const comparison: Comparison = {
  scenario: {
    id: universe.scenario_id,
    profile_id: "10000000-0000-4000-8000-000000000001",
    title: "After graduation",
    decision_question: "What should Hosein prioritize after graduation?",
    description: "Three paths",
    number_of_universes: 3,
    simulation_mode: "realistic",
    seed: 202600,
    created_at: "2026-01-01T00:00:00Z",
  },
  universes: [
    {
      universe,
      current_stats: {
        career_level: 54,
        health: 74,
        relationships: 64,
        research_impact: 50,
        reputation: 48,
        freedom: 52,
        stress: 62,
        happiness: 71,
        discipline: 84,
        creativity: 79,
        chaos: 25,
      },
      financial_position: { monthly_income_eur: 3600, net_worth_eur: 22000 },
      location: "Milan",
      career_summary: "AI Lead, level 54",
      major_achievements: ["Led a safe deployment"],
      major_regrets: ["Protected too little recovery time"],
      key_decisions: ["2027: Take the ambitious route"],
      history: [
        { year: 2026, happiness: 69, stress: 60, net_worth_eur: 14000 },
        { year: 2027, happiness: 71, stress: 62, net_worth_eur: 22000 },
      ],
      score_components: {
        wellbeing: 70,
        sustainability: 58,
        career_momentum: 62,
        research_momentum: 59,
        financial_resilience: 61,
      },
    },
  ],
};

export const conversation: FutureSelfConversation = {
  conversation: {
    id: "80000000-0000-4000-8000-000000000001",
    universe_id: universe.id,
    title: "Conversation with future Hosein",
    future_self_age: 26,
    personality_summary: "Reflective and candid.",
    created_at: "2027-01-01T00:00:00Z",
  },
  identity: {
    name: "Hosein",
    age: 26,
    location: "Milan",
    occupation: "AI Lead",
    universe: universe.name,
    key_achievement: "Led a safe deployment",
    greatest_regret: "Protected too little recovery time",
    happiness: 71,
    stress: 62,
    personality_summary: "Reflective and candid.",
    fictional_character: true,
  },
  messages: [],
  pagination: { offset: 0, limit: 100, total: 0, has_more: false },
};
