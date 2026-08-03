"use client";

import type { Artifact } from "@/lib/api/schemas";

const text = (value: unknown, fallback = "") =>
  typeof value === "string" ? value : fallback;
const number = (value: unknown) => (typeof value === "number" ? value : 0);
const strings = (value: unknown) =>
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];

export function ArtifactCard({
  artifact,
  onOpen,
}: {
  artifact: Artifact;
  onOpen?: () => void;
}) {
  const content = artifact.content;
  const layout = artifact.artifact_type;
  const body = (() => {
    switch (layout) {
      case "news_article":
        return (
          <div className="artifact-news" data-testid="artifact-news">
            <span>{text(content.publication_name, "Fictional press")}</span>
            <h3>{text(content.headline, artifact.title)}</h3>
            <p>{text(content.subheading)}</p>
          </div>
        );
      case "academic_abstract":
        return (
          <div className="artifact-paper" data-testid="artifact-paper">
            <span>RESEARCH ABSTRACT · {content.year as number}</span>
            <h3>{text(content.paper_title, artifact.title)}</h3>
            <p>{strings(content.authors).join(", ")}</p>
            <div>
              {strings(content.keywords).map((keyword) => (
                <i key={keyword}>{keyword}</i>
              ))}
            </div>
          </div>
        );
      case "company_announcement":
        return (
          <div className="artifact-company" data-testid="artifact-company">
            <span>{text(content.company)}</span>
            <h3>{text(content.headline, artifact.title)}</h3>
            <blockquote>{text(content.quote)}</blockquote>
          </div>
        );
      case "diary_entry":
        return (
          <div className="artifact-diary" data-testid="artifact-diary">
            <span>
              {text(content.date)} · {text(content.mood)}
            </span>
            <h3>{artifact.title}</h3>
            <p>{text(content.entry)}</p>
          </div>
        );
      case "email":
        return (
          <div className="artifact-email" data-testid="artifact-email">
            <dl>
              <div>
                <dt>From</dt>
                <dd>{text(content.sender)}</dd>
              </div>
              <div>
                <dt>To</dt>
                <dd>{text(content.recipient)}</dd>
              </div>
            </dl>
            <h3>{text(content.subject, artifact.title)}</h3>
            <p>{text(content.body)}</p>
          </div>
        );
      default:
        return (
          <div className="artifact-social" data-testid="artifact-social">
            <span>{text(content.platform, "Fictional social network")}</span>
            <h3>{text(content.author, artifact.title)}</h3>
            <p>{text(content.content)}</p>
            <small>
              {number(content.reactions).toLocaleString()} reactions
            </small>
          </div>
        );
    }
  })();

  return (
    <article className={`artifact-card artifact-${layout}`}>
      <span className="fictional-label">Fictional artifact</span>
      {body}
      {onOpen ? (
        <button type="button" className="artifact-open" onClick={onOpen}>
          Open artifact <span aria-hidden="true">↗</span>
        </button>
      ) : null}
    </article>
  );
}

export function ArtifactViewer({
  artifact,
  onClose,
}: {
  artifact: Artifact;
  onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className="artifact-viewer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="artifact-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <p className="eyebrow">
              {artifact.year} · {artifact.artifact_type.replaceAll("_", " ")}
            </p>
            <h2 id="artifact-title">{artifact.title}</h2>
          </div>
          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            aria-label="Close artifact"
          >
            ×
          </button>
        </header>
        <ArtifactCard artifact={artifact} />
      </div>
    </div>
  );
}
