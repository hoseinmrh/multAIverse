import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { ScenarioForm } from "@/features/scenarios/scenario-form";

export const metadata: Metadata = { title: "Create scenario" };

export default async function ScenarioPage({
  searchParams,
}: {
  searchParams: Promise<{ profile?: string }>;
}) {
  const { profile = "" } = await searchParams;
  return (
    <AppShell>
      {profile ? (
        <ScenarioForm profileId={profile} />
      ) : (
        <div className="state-panel state-error" role="alert">
          <div>
            <h1>A profile is required</h1>
            <p>Create a protagonist before opening a new scenario.</p>
          </div>
        </div>
      )}
    </AppShell>
  );
}
