"use client";

import { useEffect, useRef, useState } from "react";

import type { Choice, EventDetail } from "@/lib/api/schemas";

function effectSummary(choice: Choice): string[] {
  const results: string[] = [];
  const stats = choice.immediate_effects.stats;
  if (stats && typeof stats === "object") {
    for (const [name, amount] of Object.entries(stats)) {
      if (typeof amount === "number") {
        results.push(
          `${amount > 0 ? "+" : ""}${amount} ${name.replaceAll("_", " ")}`,
        );
      }
    }
  }
  const finance = choice.immediate_effects.finance;
  if (finance && typeof finance === "object") {
    for (const [name, amount] of Object.entries(finance)) {
      if (typeof amount === "number") {
        results.push(
          `${amount > 0 ? "+" : ""}€${amount.toLocaleString()} ${name.replaceAll("_", " ")}`,
        );
      }
    }
  }
  return results;
}

export function EventDecisionModal({
  detail,
  isSubmitting,
  onConfirm,
}: {
  detail: EventDetail;
  isSubmitting: boolean;
  onConfirm: (choiceId: string) => void;
}) {
  const [selectedId, setSelectedId] = useState(
    detail.choices.find((choice) => choice.selected)?.id ?? "",
  );
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const focusable = dialog.querySelectorAll<HTMLElement>(
      "button:not([disabled]), input:not([disabled])",
    );
    focusable[0]?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab" || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => document.removeEventListener("keydown", trap);
  }, []);

  return (
    <div className="modal-backdrop">
      <div
        ref={dialogRef}
        className="decision-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="decision-title"
        aria-describedby="decision-description"
      >
        <header>
          <div>
            <p className="eyebrow">{detail.event.year} · Important decision</p>
            <h2 id="decision-title">{detail.event.title}</h2>
          </div>
          <span className="decision-category">{detail.event.category}</span>
        </header>
        <p id="decision-description" className="decision-narrative">
          {detail.event.description}
        </p>
        <fieldset className="choice-list">
          <legend>Choose how this future responds</legend>
          {detail.choices.map((choice) => {
            const effects = effectSummary(choice);
            return (
              <label
                key={choice.id}
                className={selectedId === choice.id ? "selected" : ""}
              >
                <input
                  type="radio"
                  name="event-choice"
                  value={choice.id}
                  checked={selectedId === choice.id}
                  disabled={isSubmitting || choice.selected}
                  onChange={() => setSelectedId(choice.id)}
                />
                <span className={`risk risk-${choice.risk_level}`}>
                  {choice.risk_level} risk
                </span>
                <strong>{choice.label}</strong>
                <p>{choice.description}</p>
                {effects.length ? (
                  <ul aria-label="Known immediate consequences">
                    {effects.map((effect) => (
                      <li key={effect}>{effect}</li>
                    ))}
                  </ul>
                ) : (
                  <small>No immediate statistical change is shown.</small>
                )}
                {choice.delayed_effects.length ? (
                  <small className="uncertain-note">
                    Some long-term consequences remain uncertain.
                  </small>
                ) : null}
              </label>
            );
          })}
        </fieldset>
        <div className="modal-actions">
          <p>Your selection becomes part of the immutable timeline.</p>
          <button
            className="button button-primary"
            type="button"
            disabled={!selectedId || isSubmitting}
            onClick={() => onConfirm(selectedId)}
          >
            {isSubmitting ? "Resolving decision…" : "Confirm this choice"}
          </button>
        </div>
      </div>
    </div>
  );
}
