"use client";

import { useEffect, useState } from "react";

type ConnectionState = "checking" | "online" | "offline";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api/v1";

export function BackendStatus() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          cache: "no-store",
          signal: controller.signal,
        });
        setConnectionState(response.ok ? "online" : "offline");
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setConnectionState("offline");
        }
      }
    }

    void checkBackend();
    return () => controller.abort();
  }, []);

  const label = {
    checking: "Checking local backend…",
    online: "Backend online",
    offline: "Backend unavailable",
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
