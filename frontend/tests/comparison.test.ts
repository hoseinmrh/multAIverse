import { describe, expect, it } from "vitest";

import { buildComparisonSummary } from "@/features/comparison/comparison-view";
import { comparison } from "@/tests/fixtures";

describe("comparison data", () => {
  it("builds a non-ranking summary from backend comparison fields", () => {
    const summary = buildComparisonSummary(comparison);
    expect(summary).toContain("current happiness spans 71–71");
    expect(summary).toContain("does not declare a single best universe");
    expect(summary).not.toContain("winner");
  });
});
