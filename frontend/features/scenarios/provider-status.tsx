import type { PublicConfig } from "@/lib/api/schemas";

export function ProviderStatus({ config }: { config: PublicConfig }) {
  const status = config.narrative_provider_status;
  const isMock = config.narrative_provider === "mock";
  const isFallback = status.state === "fallback";
  const isUnavailable = status.state === "unavailable";
  const title = isMock
    ? "Mock narrative provider"
    : isFallback
      ? "Mock fallback active"
      : "OpenAI narrative provider";
  const detail = isMock
    ? "Offline, deterministic narrative templates are active. No API key is used."
    : status.detail;

  return (
    <div className="provider-status" role="status">
      <span className="provider-icon" aria-hidden="true">
        ◉
      </span>
      <div>
        <strong>{title}</strong>
        <p>{detail}</p>
        {status.model ? <small>Model: {status.model}</small> : null}
        {!isMock && status.state === "configured" ? (
          <small>
            Narrative mode:{" "}
            {status.fallback_enabled ? "GPT with mock fallback" : "GPT only"}
          </small>
        ) : null}
      </div>
      <span
        className={`status-chip ${isUnavailable ? "status-error" : "status-ready"}`}
      >
        <i aria-hidden="true" />
        {isUnavailable
          ? "Unavailable"
          : isFallback
            ? "Fallback"
            : status.state === "configured"
              ? "Configured"
              : "Ready"}
      </span>
    </div>
  );
}
