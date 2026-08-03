import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { StoryLibrary } from "@/features/scenarios/story-library";

export const metadata: Metadata = { title: "Saved stories" };

export default function StoriesPage() {
  return (
    <AppShell>
      <StoryLibrary />
    </AppShell>
  );
}
