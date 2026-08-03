import type { ZodType } from "zod";

import {
  advancementSchema,
  artifactPageSchema,
  comparisonSchema,
  eventDetailSchema,
  eventPageSchema,
  futureSelfConversationSchema,
  generationSchema,
  profilePageSchema,
  profileCreateSchema,
  profileSchema,
  publicConfigSchema,
  scenarioCreateSchema,
  scenarioDetailSchema,
  scenarioPageSchema,
  scenarioSchema,
  timelinePageSchema,
  universeSchema,
  universeStateSchema,
  type ProfileCreate,
  type ScenarioCreate,
} from "@/lib/api/schemas";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = "request_failed",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  schema: ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "The local backend is unavailable. Start it and try again.",
      0,
      "backend_unavailable",
    );
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const errorPayload = payload as {
      error?: { message?: string; code?: string };
    } | null;
    throw new ApiError(
      errorPayload?.error?.message ?? "The request could not be completed.",
      response.status,
      errorPayload?.error?.code,
    );
  }

  const parsed = schema.safeParse(payload);
  if (!parsed.success) {
    throw new ApiError(
      "The backend returned data in an unexpected format.",
      response.status,
      "invalid_response",
    );
  }
  return parsed.data;
}

const json = (value: unknown) => JSON.stringify(value);

export const api = {
  config: () => request("/config/public", publicConfigSchema),
  profiles: () => request("/profiles?limit=100", profilePageSchema),
  profile: (id: string) => request(`/profiles/${id}`, profileSchema),
  createProfile: (input: ProfileCreate) =>
    request("/profiles", profileSchema, {
      method: "POST",
      body: json(profileCreateSchema.parse(input)),
    }),
  scenarios: (profileId?: string) =>
    request(
      `/scenarios?limit=100${profileId ? `&profile_id=${profileId}` : ""}`,
      scenarioPageSchema,
    ),
  scenario: (id: string) => request(`/scenarios/${id}`, scenarioDetailSchema),
  createScenario: (input: ScenarioCreate) =>
    request("/scenarios", scenarioSchema, {
      method: "POST",
      body: json(scenarioCreateSchema.parse(input)),
    }),
  generateUniverses: (scenarioId: string) =>
    request(`/scenarios/${scenarioId}/generate-universes`, generationSchema, {
      method: "POST",
    }),
  universe: (id: string) => request(`/universes/${id}`, universeSchema),
  universeState: (id: string) =>
    request(`/universes/${id}/state`, universeStateSchema),
  timeline: (id: string) =>
    request(`/universes/${id}/timeline?limit=100`, timelinePageSchema),
  events: (id: string) =>
    request(`/universes/${id}/events?limit=100`, eventPageSchema),
  event: (id: string) => request(`/events/${id}`, eventDetailSchema),
  artifacts: (id: string) =>
    request(`/universes/${id}/artifacts?limit=100`, artifactPageSchema),
  advance: (id: string) =>
    request(`/universes/${id}/advance`, advancementSchema, { method: "POST" }),
  selectChoice: (eventId: string, choiceId: string) =>
    request(
      `/events/${eventId}/choices/${choiceId}/select`,
      advancementSchema,
      { method: "POST" },
    ),
  resetUniverse: (id: string) =>
    request(`/universes/${id}/reset`, universeStateSchema, { method: "POST" }),
  comparison: (scenarioId: string) =>
    request(`/scenarios/${scenarioId}/comparison`, comparisonSchema),
  createConversation: (universeId: string) =>
    request(
      `/universes/${universeId}/future-self/conversations`,
      futureSelfConversationSchema,
      { method: "POST", body: "{}" },
    ),
  conversation: (id: string) =>
    request(
      `/future-self/conversations/${id}?limit=100`,
      futureSelfConversationSchema,
    ),
  sendMessage: (conversationId: string, content: string) =>
    request(
      `/future-self/conversations/${conversationId}/messages?limit=100`,
      futureSelfConversationSchema,
      { method: "POST", body: json({ content }) },
    ),
};
