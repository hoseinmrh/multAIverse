export const DEMO_PROFILE_ID = "10000000-0000-4000-8000-000000000001";
export const DEMO_SCENARIO_ID = "20000000-0000-4000-8000-000000000001";

export const DISCLAIMER =
  "Multiverse creates fictional scenarios for entertainment and reflection. Its simulations are not predictions or professional advice.";

export const UNIVERSE_ACCENTS = ["#5a9cff", "#9d7cff", "#f6ad55"] as const;

export function universeAccent(
  theme: Record<string, unknown>,
  index = 0,
): string {
  return typeof theme.accent === "string"
    ? theme.accent
    : UNIVERSE_ACCENTS[index % UNIVERSE_ACCENTS.length];
}
