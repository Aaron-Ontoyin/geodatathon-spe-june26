import { useEffect, useRef, useState } from "react";

import { streamChat } from "../api/client";
import { Panel } from "./Panel";

interface ChatDockProps {
  /** Grounding context handed to the analyst (e.g. serialized dashboard state). */
  context: string;
}

interface ChatMessage {
  role: "user" | "bot";
  text: string;
}

const KEY_STORAGE = "openrouter_key";
const MAX_TURNS = 6;

/** Grounded streaming chat against the design assumptions and results. */
export function ChatDock({ context }: ChatDockProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [showKey, setShowKey] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>(() => {
    try {
      return localStorage.getItem(KEY_STORAGE) ?? "";
    } catch {
      return "";
    }
  });

  const scrollRef = useRef<HTMLDivElement>(null);

  // Persist the key as it changes; auto-scroll on every message mutation.
  useEffect(() => {
    try {
      if (apiKey) localStorage.setItem(KEY_STORAGE, apiKey);
      else localStorage.removeItem(KEY_STORAGE);
    } catch {
      /* localStorage unavailable — non-fatal */
    }
  }, [apiKey]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const appendToLastBot = (token: string): void => {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const next = prev.slice();
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, text: last.text + token };
      return next;
    });
  };

  const submit = (): void => {
    const question = input.trim();
    if (!question || busy) return;

    // Build history from prior exchanges (cap to last ~6 turns), before we push.
    const history = messages
      .slice(-MAX_TURNS * 2)
      .map(
        (m): [string, string] => [m.role === "user" ? "user" : "assistant", m.text],
      );

    setMessages((prev) => [
      ...prev,
      { role: "user", text: question },
      { role: "bot", text: "" },
    ]);
    setInput("");
    setBusy(true);

    streamChat(
      { question, history, context, api_key: apiKey || null },
      {
        onToken: (t) => appendToLastBot(t),
        onDone: () => setBusy(false),
        onError: () => setBusy(false),
      },
    );
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <Panel
      label="ASK THE ANALYST"
      accent="cool"
      right={<span className={`led ${busy ? "busy" : "off"}`} />}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--s3)" }}>
        <div
          ref={scrollRef}
          style={{
            maxHeight: 320,
            minHeight: 120,
            overflowY: "auto",
            paddingRight: 4,
          }}
        >
          {messages.length === 0 ? (
            <div
              className="label"
              style={{
                color: "var(--text-faint)",
                padding: "32px 8px",
                textAlign: "center",
              }}
            >
              Ask about the resource, design, or economics
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                <div className="who">{m.role === "user" ? "YOU" : "ANALYST"}</div>
                <div className="bubble" style={{ whiteSpace: "pre-wrap" }}>
                  {m.text}
                  {busy && m.role === "bot" && i === messages.length - 1 && !m.text ? (
                    <span style={{ color: "var(--text-faint)" }}>&hellip;</span>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="field-row" style={{ gap: "var(--s2)", marginBottom: 0 }}>
          <div className="field" style={{ flex: 1, marginBottom: 0 }}>
            <input
              type="text"
              value={input}
              placeholder="Type a question&hellip;"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={busy}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={submit}
            disabled={busy || !input.trim()}
          >
            ASK
          </button>
        </div>

        <div>
          <button
            className="btn"
            style={{
              fontSize: 10,
              padding: "3px 8px",
              background: "transparent",
              border: "none",
              color: "var(--text-faint)",
            }}
            onClick={() => setShowKey((v) => !v)}
          >
            {showKey ? "HIDE KEY" : "SET KEY"}
          </button>
          {showKey ? (
            <div className="field" style={{ marginTop: "var(--s2)", marginBottom: 0 }}>
              <input
                type="password"
                value={apiKey}
                placeholder="OpenRouter API key (optional)"
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          ) : null}
        </div>
      </div>
    </Panel>
  );
}
