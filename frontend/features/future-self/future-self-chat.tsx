"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { ErrorState, LoadingState } from "@/components/ui/async-state";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queries";

const suggestions = [
  "What decision changed your life most?",
  "What do you regret?",
  "Was this path worth it?",
  "What did you sacrifice?",
  "What would you tell your younger self?",
];

export function FutureSelfChat({
  universeId,
  scenarioId,
}: {
  universeId: string;
  scenarioId: string;
}) {
  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState("");
  const [draft, setDraft] = useState("");
  const started = useRef(false);
  const endRef = useRef<HTMLDivElement>(null);

  const createConversation = useMutation({
    mutationFn: () => api.createConversation(universeId),
    onSuccess: (data) => {
      setConversationId(data.conversation.id);
      queryClient.setQueryData(
        queryKeys.conversation(data.conversation.id),
        data,
      );
    },
  });

  useEffect(() => {
    if (!started.current) {
      started.current = true;
      createConversation.mutate();
    }
  }, [createConversation]);

  const conversation = useQuery({
    queryKey: queryKeys.conversation(conversationId),
    queryFn: () => api.conversation(conversationId),
    enabled: Boolean(conversationId),
  });

  const sendMessage = useMutation({
    mutationFn: (content: string) => api.sendMessage(conversationId, content),
    onSuccess: async (data) => {
      queryClient.setQueryData(queryKeys.conversation(conversationId), data);
      setDraft("");
      await queryClient.invalidateQueries({
        queryKey: queryKeys.conversation(conversationId),
      });
    },
  });

  const messages = conversation.data?.messages;
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const content = draft.trim();
    if (content && !sendMessage.isPending) sendMessage.mutate(content);
  };

  if (
    createConversation.isPending ||
    (conversationId && conversation.isPending)
  ) {
    return <LoadingState label="Connecting to this fictional future self…" />;
  }
  if (createConversation.isError) {
    return (
      <ErrorState
        error={createConversation.error}
        onRetry={() => createConversation.mutate()}
      />
    );
  }
  if (conversation.isError) {
    return (
      <ErrorState
        error={conversation.error}
        onRetry={() => void conversation.refetch()}
      />
    );
  }
  if (!conversation.data) return null;

  const { identity } = conversation.data;
  return (
    <section className="chat-page" aria-labelledby="chat-title">
      <aside className="future-identity panel">
        <Link
          className="back-link"
          href={`/universe/${universeId}?scenario=${scenarioId}`}
        >
          ← Back to universe
        </Link>
        <div className="future-avatar" aria-hidden="true">
          {identity.name.slice(0, 1)}
        </div>
        <span className="fictional-label">Fictional generated character</span>
        <h1 id="chat-title">{identity.name}</h1>
        <p>
          {identity.age} years old · {identity.location}
        </p>
        <strong>{identity.occupation}</strong>
        <small>{identity.universe}</small>
        <dl>
          <div>
            <dt>Key achievement</dt>
            <dd>{identity.key_achievement}</dd>
          </div>
          <div>
            <dt>Greatest regret</dt>
            <dd>{identity.greatest_regret}</dd>
          </div>
          <div>
            <dt>Happiness</dt>
            <dd>{identity.happiness}/100</dd>
          </div>
          <div>
            <dt>Stress</dt>
            <dd>{identity.stress}/100</dd>
          </div>
        </dl>
        <p className="personality-note">{identity.personality_summary}</p>
      </aside>

      <div className="chat-panel panel">
        <header>
          <div>
            <p className="eyebrow">A conversation across time</p>
            <h2>{conversation.data.conversation.title}</h2>
          </div>
          <span className="status-chip">
            <i aria-hidden="true" /> Mock provider
          </span>
        </header>
        <div
          className="message-list"
          aria-live="polite"
          aria-label="Conversation messages"
        >
          {!conversation.data.messages.length ? (
            <div className="chat-empty">
              <span aria-hidden="true">✦</span>
              <h3>What do you want to know?</h3>
              <p>
                Replies stay grounded in this universe&apos;s stored timeline
                and current statistics.
              </p>
            </div>
          ) : null}
          {conversation.data.messages.map((message) => (
            <article
              key={message.id}
              className={`message message-${message.role}`}
            >
              <span>
                {message.role === "user" ? "You, now" : identity.name}
              </span>
              <p>{message.content}</p>
            </article>
          ))}
          {sendMessage.isPending ? (
            <div
              className="message message-future_self message-typing"
              role="status"
            >
              <span>{identity.name}</span>
              <p>Thinking across the timeline…</p>
            </div>
          ) : null}
          <div ref={endRef} />
        </div>
        <div className="suggestion-row" aria-label="Suggested questions">
          {suggestions.map((suggestion) => (
            <button
              type="button"
              key={suggestion}
              disabled={sendMessage.isPending}
              onClick={() => sendMessage.mutate(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
        {sendMessage.isError ? (
          <p className="form-error" role="alert">
            {sendMessage.error.message}
          </p>
        ) : null}
        <form className="chat-composer" onSubmit={submit}>
          <label className="sr-only" htmlFor="future-message">
            Message your fictional future self
          </label>
          <textarea
            id="future-message"
            value={draft}
            maxLength={2_000}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Ask about this path…"
          />
          <button
            className="button button-primary"
            type="submit"
            disabled={!draft.trim() || sendMessage.isPending}
          >
            Send <span aria-hidden="true">↑</span>
          </button>
        </form>
      </div>
    </section>
  );
}
