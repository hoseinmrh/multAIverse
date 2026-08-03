import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { SettingsScreen } from "@/features/scenarios/settings-screen";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <AppShell>
      <SettingsScreen />
    </AppShell>
  );
}
