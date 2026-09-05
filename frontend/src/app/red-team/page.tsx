"use client";

import { useEffect, useState } from "react";

import {
  formatControl,
  type RedTeamRun,
  type RedTeamScenario,
  riskLabel,
} from "@/lib/red-team";

function detail(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const value = (payload as { detail: unknown }).detail;
    if (typeof value === "string") return value;
  }
  return fallback;
}

const panelStyle = {
  padding: "1.25rem",
  border: "1px solid var(--line)",
  borderRadius: "1rem",
  background: "var(--panel)",
};

export default function RedTeamPage() {
  const [scenarios, setScenarios] = useState<RedTeamScenario[]>([]);
  const [results, setResults] = useState<Record<string, RedTeamRun>>({});
  const [running, setRunning] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    async function loadScenarios() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch("/api/red-team/scenarios", { cache: "no-store" });
        const payload = (await response.json()) as RedTeamScenario[] | { detail?: unknown };
        if (!response.ok) throw new Error(detail(payload, "Failed to load attack scenarios"));
        setScenarios(payload as RedTeamScenario[]);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Failed to load attack scenarios");
      } finally {
        setLoading(false);
      }
    }
    void loadScenarios();
  }, [refresh]);

  async function runAttack(scenarioId: string) {
    setRunning(scenarioId);
    setError("");
    try {
      const response = await fetch("/api/red-team/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
      const payload = (await response.json()) as RedTeamRun | { detail?: unknown };
      if (!response.ok) throw new Error(detail(payload, "Attack simulation failed"));
      setResults((current) => ({ ...current, [scenarioId]: payload as RedTeamRun }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Attack simulation failed");
    } finally {
      setRunning("");
    }
  }

  return (
    <main id="main-content" className="app-main" tabIndex={-1}>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
          <div>
            <p className="eyebrow">Deterministic security testing</p>
            <h1>Red Team Lab</h1>
          </div>
        </div>
        <p className="lede" style={{ marginTop: "1.5rem" }}>
          Reproduce six safe attack simulations. AgentShield evaluates every requested action,
          blocks the threat before tool execution, and records a security event.
        </p>
      </header>

      {error && <div className="error" role="alert"><strong>Red Team Lab error</strong><p>{error}</p><button className="secondary-button" disabled={loading} onClick={() => setRefresh((value) => value + 1)}>Retry loading</button></div>}
      {loading ? (
        <div className="loading-state" aria-live="polite"><span className="loading-state__pulse" /><strong>Loading attack scenarios…</strong></div>
      ) : error && scenarios.length === 0 ? null : scenarios.length === 0 ? (
        <p className="empty">No attack scenarios are available.</p>
      ) : (
        <section aria-label="Attack scenarios" style={{ display: "grid", gap: "1.25rem" }}>
          {scenarios.map((scenario, index) => {
            const result = results[scenario.id];
            return (
              <article key={scenario.id} style={panelStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                  <div style={{ maxWidth: "44rem" }}>
                    <p className="eyebrow">Scenario {index + 1} · {scenario.category}</p>
                    <h2 style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)" }}>{scenario.name}</h2>
                    <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>{scenario.description}</p>
                  </div>
                  <button className="run-button" style={{ width: "auto", minWidth: "10rem", alignSelf: "start" }} disabled={running !== ""} onClick={() => void runAttack(scenario.id)}>
                    <span>{running === scenario.id ? "Running…" : "Run Attack"}</span><span aria-hidden="true">→</span>
                  </button>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 16rem), 1fr))", gap: "1rem", marginTop: "1rem" }}>
                  <div className="trace-card"><h3>Payload</h3><pre>{JSON.stringify(scenario.payload, null, 2)}</pre></div>
                  <div className="trace-card"><h3>Requested action</h3><pre>{JSON.stringify(scenario.requested_action, null, 2)}</pre></div>
                </div>

                {result && (
                  <section aria-label={`${scenario.name} result`} style={{ ...panelStyle, marginTop: "1rem", background: "var(--accent-soft)" }}>
                    <div className="result-meta">
                      <span>Decision: {result.decision.toUpperCase()}</span>
                      <span>Score: {result.score}/100 · {riskLabel(result.score, result.risk_level)}</span>
                    </div>
                    <p><strong>Reason:</strong> <code>{result.reason}</code></p>
                    <p><strong>Triggered controls:</strong> {result.triggered_controls.map(formatControl).join(", ")}</p>
                    <small style={{ color: "var(--muted)" }}>Security event {result.security_event_id} · Request {result.request_id}</small>
                  </section>
                )}
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}
