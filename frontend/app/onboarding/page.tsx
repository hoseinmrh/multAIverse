import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { ProfileForm } from "@/features/onboarding/profile-form";

export const metadata: Metadata = { title: "Create profile" };

export default function OnboardingPage() {
  return (
    <AppShell wide>
      <ProfileForm />
    </AppShell>
  );
}
