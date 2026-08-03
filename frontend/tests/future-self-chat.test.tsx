import { fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FutureSelfChat } from "@/features/future-self/future-self-chat";
import { api } from "@/lib/api/client";
import { conversation, universe } from "@/tests/fixtures";
import { renderWithQuery } from "@/tests/utils";

describe("FutureSelfChat", () => {
  afterEach(() => vi.restoreAllMocks());

  it("creates a server conversation and refreshes after a message", async () => {
    vi.spyOn(api, "createConversation").mockResolvedValue(conversation);
    const updated = {
      ...conversation,
      messages: [
        {
          id: "81000000-0000-4000-8000-000000000001",
          conversation_id: conversation.conversation.id,
          role: "user" as const,
          content: "What do you regret?",
          state_snapshot_id: null,
          created_at: "2027-01-02T00:00:00Z",
        },
        {
          id: "81000000-0000-4000-8000-000000000002",
          conversation_id: conversation.conversation.id,
          role: "future_self" as const,
          content: "I regret treating recovery as optional.",
          state_snapshot_id: null,
          created_at: "2027-01-02T00:00:01Z",
        },
      ],
      pagination: { ...conversation.pagination, total: 2 },
    };
    vi.spyOn(api, "conversation")
      .mockResolvedValueOnce(conversation)
      .mockResolvedValue(updated);
    vi.spyOn(api, "sendMessage").mockResolvedValue(updated);
    renderWithQuery(
      <FutureSelfChat
        universeId={universe.id}
        scenarioId={universe.scenario_id}
      />,
    );

    expect(
      await screen.findByText("Fictional generated character"),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "What do you regret?" }),
    );
    expect(
      await screen.findByText("I regret treating recovery as optional."),
    ).toBeInTheDocument();
    expect(api.sendMessage).toHaveBeenCalledWith(
      conversation.conversation.id,
      "What do you regret?",
    );
  });
});
