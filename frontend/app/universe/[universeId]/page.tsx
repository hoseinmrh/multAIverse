import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { UniverseDetail } from "@/features/universes/universe-detail";

export const metadata: Metadata = { title: "Universe" };

export default async function UniversePage({
  params,
  searchParams,
}: {
  params: Promise<{ universeId: string }>;
  searchParams: Promise<{ scenario?: string }>;
}) {
  const [{ universeId }, { scenario = "" }] = await Promise.all([
    params,
    searchParams,
  ]);
  return (
    <AppShell wide>
      <UniverseDetail universeId={universeId} scenarioId={scenario} />
    </AppShell>
  );
}
