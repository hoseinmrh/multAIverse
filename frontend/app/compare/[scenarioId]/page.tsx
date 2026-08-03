import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { ComparisonView } from "@/features/comparison/comparison-view";

export const metadata: Metadata = { title: "Compare universes" };

export default async function ComparePage({
  params,
}: {
  params: Promise<{ scenarioId: string }>;
}) {
  const { scenarioId } = await params;
  return (
    <AppShell wide>
      <ComparisonView scenarioId={scenarioId} />
    </AppShell>
  );
}
