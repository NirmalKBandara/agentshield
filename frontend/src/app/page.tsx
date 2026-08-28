"use client";

import { FormEvent, useEffect, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AgentResult, presentAgentResult } from "@/lib/agent-result";

type ConnectionState = "checking" | "connected" | "unavailable";

const examples = [
  "Show customer 1002",
  "Refund order ORD-1002 amount 25.00",
  "Fetch https://docs.agentshield.local/",
];

export default function Home() {
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
      } catch { setConnection("unavailable"); }
    }
    void checkBackend();
  }, []);

  async function runAgent(event: FormEvent) {
    event.preventDefault();
    setRunning(true); setError(""); setResult(null);
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
    } finally { setRunning(false); }
  }

  const presentation = result ? presentAgentResult(result) : null;

  return (
    <main>
      <div className="shell">
        <header className="nav">
          <a className="brand" href="#top">AgentShield<span>.</span></a>
          <ThemeToggle />
        </header>
        <section className="hero" id="top">
          <div>
            <p className="eyebrow">AI agent security gateway</p>
            <h1>Tools, under<br /><em>control.</em></h1>
            <p className="lede">A deliberately small, inspectable agent stack for testing secure tool execution. Every demo action stays local and uses fictional data.</p>
          </div>
          <div className={`status status--${connection}`} role="status" aria-live="polite">
            <span className="status__dot" aria-hidden="true" />
            <div><strong>Frontend → Backend</strong><p>
              {connection === "checking" && "Checking connection…"}
              {connection === "connected" && `Connected to ${service}`}
              {connection === "unavailable" && "Backend unavailable"}
            </p></div>
          </div>
        </section>
        <section className="playground" aria-labelledby="playground-title">
          <div className="section-heading"><p className="eyebrow">Day 06 / Live flow</p><h2 id="playground-title">Agent playground</h2></div>
          <div className="workspace">
            <form onSubmit={runAgent} aria-describedby="prompt-help">
              <label htmlFor="prompt">Natural-language request</label>
              <p className="field-help" id="prompt-help">Ask the demo agent to look up a customer, send a fictional email, issue a demo refund, or fetch a safe URL.</p>
              <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={4000} required disabled={running} />
              <div className="examples" aria-label="Example prompts">
                {examples.map((example) => <button type="button" key={example} onClick={() => setPrompt(example)} disabled={running}>{example}</button>)}
              </div>
              <button className="run-button" type="submit" disabled={running || !prompt.trim()}>
                {running ? <><span className="spinner" aria-hidden="true" />Routing request…</> : <>Run demo agent<span aria-hidden="true">→</span></>}
              </button>
            </form>
            <div className="result-panel" aria-busy={running}>
              <span className="result-label">Execution trace</span>
              {running && <div className="loading-state" role="status" aria-live="polite"><span className="loading-state__pulse" aria-hidden="true" /><div><strong>Agent is deciding what to do</strong><p>Validating the request and selecting a demo tool…</p></div></div>}
              {!running && !result && !error && <p className="empty">Run a request to see the agent response, requested tool, arguments, and tool result.</p>}
              {!running && error && <div className="error" role="alert"><strong>Request could not be completed</strong><p>{error}</p><p className="error__hint">Check that the backend is running, then try again.</p></div>}
              {!running && result && presentation && <div className="trace" aria-live="polite">
                <div className="result-meta" aria-label="Execution metadata"><span>{result.decision.action === "tool" ? "Tool request" : "Direct response"}</span><span>{result.provider}</span>{result.request_id && <span>Request {result.request_id}</span>}</div>
                <section className="trace-card trace-card--summary" aria-labelledby="agent-response-title"><h3 id="agent-response-title">Agent response</h3><p>{presentation.summary}</p></section>
                <section className="trace-card" aria-labelledby="requested-tool-title"><h3 id="requested-tool-title">Requested tool</h3><code className="tool-name">{presentation.toolName}</code></section>
                <section className="trace-card" aria-labelledby="arguments-title"><h3 id="arguments-title">Arguments</h3><pre>{presentation.argumentsText}</pre></section>
                <section className="trace-card trace-card--result" aria-labelledby="tool-result-title"><h3 id="tool-result-title">Tool result</h3><pre>{presentation.toolResultText}</pre></section>
              </div>}
            </div>
          </div>
        </section>
        <footer>Day 01–06 foundation · Four controlled tools · Zero real-world side effects</footer>
      </div>
    </main>
  );
}
