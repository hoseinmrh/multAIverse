import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { FutureSelfChat } from "@/features/future-self/future-self-chat";

export const metadata: Metadata = { title: "Future-self chat" };

export default async function FutureSelfPage({
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
      <FutureSelfChat universeId={universeId} scenarioId={scenario} />
    </AppShell>
  );
}
