"use client";

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { api } from "@/lib/api/client";
import type { ProfileCreate, ScenarioCreate } from "@/lib/api/schemas";

export const queryKeys = {
  config: ["config"] as const,
  profiles: ["profiles"] as const,
  scenario: (id: string) => ["scenario", id] as const,
  universe: (id: string) => ["universe", id] as const,
  state: (id: string) => ["universe", id, "state"] as const,
  timeline: (id: string) => ["universe", id, "timeline"] as const,
  events: (id: string) => ["universe", id, "events"] as const,
  artifacts: (id: string) => ["universe", id, "artifacts"] as const,
  comparison: (id: string) => ["scenario", id, "comparison"] as const,
  conversation: (id: string) => ["conversation", id] as const,
};

export function usePublicConfig() {
  return useQuery({ queryKey: queryKeys.config, queryFn: api.config });
}

export function useProfiles() {
  return useQuery({ queryKey: queryKeys.profiles, queryFn: api.profiles });
}

export function useScenario(id: string) {
  return useQuery({
    queryKey: queryKeys.scenario(id),
    queryFn: () => api.scenario(id),
    enabled: Boolean(id),
  });
}

export function useUniverseBundle(id: string) {
  return useQueries({
    queries: [
      { queryKey: queryKeys.state(id), queryFn: () => api.universeState(id) },
      { queryKey: queryKeys.timeline(id), queryFn: () => api.timeline(id) },
      { queryKey: queryKeys.events(id), queryFn: () => api.events(id) },
      { queryKey: queryKeys.artifacts(id), queryFn: () => api.artifacts(id) },
    ],
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileCreate) => api.createProfile(input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.profiles }),
  });
}

export function useCreateScenario() {
  return useMutation({
    mutationFn: async (input: ScenarioCreate) => {
      const scenario = await api.createScenario(input);
      await api.generateUniverses(scenario.id);
      return scenario;
    },
  });
}

export function useRefreshUniverse(universeId: string, scenarioId: string) {
  const queryClient = useQueryClient();
  return async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: queryKeys.universe(universeId),
      }),
      queryClient.invalidateQueries({ queryKey: queryKeys.state(universeId) }),
      queryClient.invalidateQueries({
        queryKey: queryKeys.timeline(universeId),
      }),
      queryClient.invalidateQueries({ queryKey: queryKeys.events(universeId) }),
      queryClient.invalidateQueries({
        queryKey: queryKeys.artifacts(universeId),
      }),
      queryClient.invalidateQueries({
        queryKey: queryKeys.scenario(scenarioId),
      }),
      queryClient.invalidateQueries({
        queryKey: queryKeys.comparison(scenarioId),
      }),
    ]);
  };
}
