import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { MultiverseMap } from "@/features/universes/multiverse-map";

export const metadata: Metadata = { title: "Multiverse map" };

export default async function MultiversePage({
  params,
}: {
  params: Promise<{ scenarioId: string }>;
}) {
  const { scenarioId } = await params;
  return (
    <AppShell wide>
      <MultiverseMap scenarioId={scenarioId} />
    </AppShell>
  );
}
