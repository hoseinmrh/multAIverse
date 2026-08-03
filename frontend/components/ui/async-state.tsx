"use client";

export function LoadingState({
  label = "Loading this reality…",
}: {
  label?: string;
}) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <span className="loading-orbit" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const message =
    error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div className="state-panel state-error" role="alert">
      <span className="state-symbol" aria-hidden="true">
        !
      </span>
      <div>
        <h2>This reality did not load</h2>
        <p>{message}</p>
        {onRetry ? (
          <button
            className="button button-secondary"
            onClick={onRetry}
            type="button"
          >
            Try again
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="state-panel">
      <span className="state-symbol" aria-hidden="true">
        ∅
      </span>
      <div>
        <h2>{title}</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}
