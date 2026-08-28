"use client";

import { FormEvent, useEffect, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";

type ConnectionState = "checking" | "connected" | "unavailable";
type AgentResult = {
  decision: { action: "tool" | "respond"; tool_name?: string; arguments: object; response?: string };
  tool_result: object | null;
  provider: string;
};

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
          <div className="section-heading"><p className="eyebrow">Day 05 / Live flow</p><h2 id="playground-title">Agent playground</h2></div>
          <div className="workspace">
            <form onSubmit={runAgent}>
              <label htmlFor="prompt">Natural-language request</label>
              <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
              <div className="examples" aria-label="Example prompts">
                {examples.map((example) => <button type="button" key={example} onClick={() => setPrompt(example)}>{example}</button>)}
              </div>
              <button className="run-button" type="submit" disabled={running || !prompt.trim()}>
                {running ? "Routing request…" : "Run demo agent"}<span aria-hidden="true">→</span>
              </button>
            </form>
            <div className="result-panel" aria-live="polite">
              <span className="result-label">Structured result</span>
              {!result && !error && <p className="empty">The selected tool and validated result will appear here.</p>}
              {error && <p className="error">{error}</p>}
              {result && <><div className="result-meta"><span>{result.decision.action}</span><span>{result.provider}</span></div><pre>{JSON.stringify(result, null, 2)}</pre></>}
            </div>
          </div>
        </section>
        <footer>Day 01–05 foundation · Four controlled tools · Zero real-world side effects</footer>
      </div>
    </main>
  );
}
