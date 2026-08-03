"use client";

import { usePublicConfig } from "@/lib/api/queries";

export function BackendStatus() {
  const config = usePublicConfig();
  const connectionState = config.isPending
    ? "checking"
    : config.isSuccess
      ? "online"
      : "offline";

  const label = {
    checking: "Checking local backend…",
    online: `${config.data?.narrative_provider === "mock" ? "Offline narrative" : "Backend"} ready`,
    offline: "Local backend unavailable",
  }[connectionState];

  return (
    <div
      className={`status status-${connectionState}`}
      role="status"
      aria-live="polite"
    >
      <span className="status-dot" aria-hidden="true" />
      {label}
    </div>
  );
}
