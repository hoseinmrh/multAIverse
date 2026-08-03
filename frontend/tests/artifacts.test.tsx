import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ArtifactCard } from "@/features/artifacts/artifact-card";
import { artifact } from "@/tests/fixtures";

describe("artifact layouts", () => {
  it.each([
    [
      "news_article",
      {
        publication_name: "Review",
        headline: "A headline",
        subheading: "A turn",
      },
      "artifact-news",
    ],
    [
      "academic_abstract",
      {
        year: 2027,
        paper_title: "A paper",
        authors: ["Hosein"],
        keywords: ["AI"],
      },
      "artifact-paper",
    ],
    [
      "company_announcement",
      { company: "Northstar", headline: "A chapter", quote: "A quote" },
      "artifact-company",
    ],
    [
      "diary_entry",
      { date: "2027-01-01", mood: "clear", entry: "A private reflection" },
      "artifact-diary",
    ],
    [
      "email",
      {
        sender: "Marta",
        recipient: "Hosein",
        subject: "Decision",
        body: "Notes",
      },
      "artifact-email",
    ],
    [
      "social_media_post",
      {
        platform: "Network",
        author: "Hosein",
        content: "A lesson",
        reactions: 42,
      },
      "artifact-social",
    ],
  ])("uses the %s visual contract", (type, content, testId) => {
    render(<ArtifactCard artifact={artifact(type, content)} />);
    expect(screen.getByTestId(testId)).toBeInTheDocument();
    expect(screen.getByText("Fictional artifact")).toBeInTheDocument();
  });
});
