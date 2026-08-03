import type { PublicConfig } from "@/lib/api/schemas";

export function ProviderStatus({ config }: { config: PublicConfig }) {
  return (
    <div className="provider-status" role="status">
      <span className="provider-icon" aria-hidden="true">
        ◉
      </span>
      <div>
        <strong>
          {config.narrative_provider === "mock"
            ? "Mock narrative provider"
            : "Narrative provider"}
        </strong>
        <p>
          Offline, deterministic narrative templates are active. No API key is
          used.
        </p>
      </div>
      <span className="status-chip status-ready">
        <i aria-hidden="true" /> Ready
      </span>
    </div>
  );
}
