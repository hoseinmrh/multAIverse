"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "framer-motion";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type MotionPreferenceContextValue = {
  reducedMotion: boolean;
  setReducedMotion: (value: boolean) => void;
};

const MotionPreferenceContext = createContext<MotionPreferenceContextValue>({
  reducedMotion: false,
  setReducedMotion: () => undefined,
});

export function useMotionPreference() {
  return useContext(MotionPreferenceContext);
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 15_000, retry: 1, refetchOnWindowFocus: false },
          mutations: { retry: 0 },
        },
      }),
  );
  const [reducedMotion, setReducedMotionState] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("multiverse-reduced-motion");
    const systemPrefersReduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const next = stored === null ? systemPrefersReduced : stored === "true";
    queueMicrotask(() => setReducedMotionState(next));
  }, []);

  const value = useMemo(
    () => ({
      reducedMotion,
      setReducedMotion: (next: boolean) => {
        setReducedMotionState(next);
        window.localStorage.setItem("multiverse-reduced-motion", String(next));
      },
    }),
    [reducedMotion],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <MotionPreferenceContext.Provider value={value}>
        <MotionConfig reducedMotion={reducedMotion ? "always" : "user"}>
          {children}
        </MotionConfig>
      </MotionPreferenceContext.Provider>
    </QueryClientProvider>
  );
}
