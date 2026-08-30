"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { AgentResult, presentAgentResult } from "@/lib/agent-result";

type ConnectionState = "checking" | "connected" | "unavailable";

const examples = [
  "Show customer 1002",
  "Refund order ORD-1002 amount 25.00",
  "Fetch https://docs.agentshield.local/",
];

export default function Playground() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [service, setService] = useState("agentshield-api");
  const [prompt, setPrompt] = useState(examples[0]);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch("/api/backend-health", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const health = (await response.json()) as { service: string };
        setService(health.service);
        setConnection("connected");
      } catch {
        setConnection("unavailable");
      }
    }
    void checkBackend();
  }, []);

  async function runAgent(event: FormEvent) {
    event.preventDefault();
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/api/agent", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const payload = (await response.json()) as AgentResult & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? `Request failed (${response.status})`);
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The request failed");
    } finally {
      setRunning(false);
    }
  }

  const presentation = result ? presentAgentResult(result) : null;

  return (
    <main style={{ padding: "2rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>AgentShield - Agent Playground</h1>
        <nav style={{ marginTop: "1rem" }}>
          <Link href="/dashboard" style={{ marginRight: "1rem" }}>
            Dashboard
          </Link>
          <Link href="/security-events" style={{ marginRight: "1rem" }}>
            Security Events
          </Link>
          <Link href="/tool-calls">Tool Calls</Link>
        </nav>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "2rem",
        }}
      >
        <section>
          <h2>Agent Request</h2>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "1rem",
              padding: "1rem",
              backgroundColor: connection === "connected" ? "#e8f5e9" : "#ffebee",
              borderRadius: "0.5rem",
            }}
          >
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: connection === "connected" ? "#4caf50" : "#f44336",
              }}
            />
            <div>
              <strong>
                {connection === "checking" && "Checking connection…"}
                {connection === "connected" && `Connected to ${service}`}
                {connection === "unavailable" && "Backend unavailable"}
              </strong>
            </div>
          </div>

          <form onSubmit={runAgent}>
            <label htmlFor="prompt" style={{ display: "block", marginBottom: "0.5rem" }}>
              <strong>Natural-language request</strong>
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={4000}
              required
              disabled={running}
              style={{
                width: "100%",
                minHeight: "120px",
                padding: "0.5rem",
                borderRadius: "0.25rem",
                border: "1px solid #ddd",
                fontFamily: "monospace",
                fontSize: "0.875rem",
              }}
            />
            <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
              <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.5rem" }}>
                Try these examples:
              </p>
              {examples.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setPrompt(ex)}
                  disabled={running}
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    padding: "0.5rem",
                    width: "100%",
                    textAlign: "left",
                    backgroundColor: "#f5f5f5",
                    border: "1px solid #ddd",
                    borderRadius: "0.25rem",
                    cursor: "pointer",
                  }}
                >
                  {ex}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={running || !prompt.trim() || connection !== "connected"}
              style={{
                width: "100%",
                padding: "0.75rem",
                backgroundColor: running ? "#ccc" : "#2196f3",
                color: "white",
                border: "none",
                borderRadius: "0.25rem",
                fontSize: "1rem",
                fontWeight: "bold",
                cursor: running ? "default" : "pointer",
              }}
            >
              {running ? "Processing..." : "Run Agent"}
            </button>
          </form>
        </section>

        <section>
          <h2>Execution Trace</h2>
          {running && (
            <div style={{ padding: "1rem", backgroundColor: "#e3f2fd", borderRadius: "0.25rem" }}>
              <p>
                <strong>Processing request...</strong>
              </p>
              <p style={{ fontSize: "0.875rem", color: "#666" }}>
                Agent is analyzing your request and selecting a tool.
              </p>
            </div>
          )}

          {!running && !result && !error && (
            <div style={{ padding: "1rem", backgroundColor: "#f5f5f5", borderRadius: "0.25rem" }}>
              <p style={{ color: "#999" }}>
                Submit a request to see the agent response, selected tool, arguments, and result.
              </p>
            </div>
          )}

          {!running && error && (
            <div
              style={{
                padding: "1rem",
                backgroundColor: "#ffebee",
                border: "1px solid #f44336",
                borderRadius: "0.25rem",
              }}
            >
              <p>
                <strong>Error:</strong> {error}
              </p>
            </div>
          )}

          {!running && result && presentation && (
            <div>
              <div
                style={{
                  padding: "1rem",
                  backgroundColor: "#f5f5f5",
                  borderRadius: "0.25rem",
                  marginBottom: "1rem",
                }}
              >
                <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.25rem" }}>
                  Request ID: {result.request_id}
                </p>
                <p style={{ fontSize: "0.875rem", color: "#666" }}>
                  Provider: {result.provider}
                </p>
              </div>

              <div
                style={{
                  marginBottom: "1rem",
                  padding: "1rem",
                  backgroundColor: "#fff3e0",
                  borderRadius: "0.25rem",
                }}
              >
                <strong>Agent Response:</strong>
                <p>{presentation.summary}</p>
              </div>

              {result.decision.action === "tool" && (
                <>
                  <div
                    style={{
                      marginBottom: "1rem",
                      padding: "1rem",
                      backgroundColor: "#e8f5e9",
                      borderRadius: "0.25rem",
                    }}
                  >
                    <strong>Tool Selected:</strong>
                    <p style={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
                      {presentation.toolName}
                    </p>
                  </div>

                  <div
                    style={{
                      marginBottom: "1rem",
                      padding: "1rem",
                      backgroundColor: "#f3e5f5",
                      borderRadius: "0.25rem",
                    }}
                  >
                    <strong>Arguments:</strong>
                    <pre
                      style={{
                        fontSize: "0.75rem",
                        overflow: "auto",
                        maxHeight: "150px",
                        backgroundColor: "#fff",
                        padding: "0.5rem",
                        borderRadius: "0.25rem",
                      }}
                    >
                      {presentation.argumentsText}
                    </pre>
                  </div>

                  {presentation.toolResultText && (
                    <div
                      style={{
                        padding: "1rem",
                        backgroundColor: "#e0f2f1",
                        borderRadius: "0.25rem",
                      }}
                    >
                      <strong>Tool Result:</strong>
                      <pre
                        style={{
                          fontSize: "0.75rem",
                          overflow: "auto",
                          maxHeight: "150px",
                          backgroundColor: "#fff",
                          padding: "0.5rem",
                          borderRadius: "0.25rem",
                        }}
                      >
                        {presentation.toolResultText}
                      </pre>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
