import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BackendStatus } from "@/components/backend-status";

describe("BackendStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reports when the backend is healthy", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));

    render(<BackendStatus />);

    expect(screen.getByText("Checking local backend…")).toBeInTheDocument();
    expect(await screen.findByText("Backend online")).toBeInTheDocument();
  });

  it("shows a recoverable unavailable state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("connection refused")),
    );

    render(<BackendStatus />);

    expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
  });
});
