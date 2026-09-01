"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  buildToolCallsQuery,
  decisionColor,
  formatArguments,
  type ToolCall,
} from "@/lib/tool-calls";

const filterControlStyle = {
  minWidth: "12rem",
  padding: ".55rem",
  color: "var(--ink)",
  border: "1px solid var(--line)",
  borderRadius: ".4rem",
  background: "var(--panel)",
};

export default function ToolCallsPage() {
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [agent, setAgent] = useState("");
  const [tool, setTool] = useState("");
  const [decision, setDecision] = useState("");
  const [selectedCall, setSelectedCall] = useState<ToolCall | null>(null);

  useEffect(() => {
    async function loadToolCalls() {
      setLoading(true);
      setError("");
      try {
        const query = buildToolCallsQuery({ agent, tool, decision });
        const response = await fetch(`/api/tool-calls${query}`);
        if (!response.ok) throw new Error("Failed to load tool calls");
        setToolCalls((await response.json()) as ToolCall[]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading tool calls");
      } finally {
        setLoading(false);
      }
    }
    void loadToolCalls();
  }, [agent, tool, decision]);

  return (
    <main style={{ padding: "2rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>Tool Calls</h1>
        <p style={{ color: "var(--muted)", maxWidth: "48rem", lineHeight: 1.6 }}>
          Inspect every agent action, the gateway decision, risk, and safely masked inputs.
        </p>
        <nav style={{ marginTop: "1rem" }}>
          <Link href="/" style={{ marginRight: "1rem" }}>Home</Link>
          <Link href="/dashboard" style={{ marginRight: "1rem" }}>Dashboard</Link>
          <Link href="/playground" style={{ marginRight: "1rem" }}>Playground</Link>
          <Link href="/security-events">Security Events</Link>
        </nav>
      </header>

      {error && (
        <div className="error" role="alert">
          <strong>Tool calls unavailable</strong>
          <p>{error}</p>
        </div>
      )}

      <section style={{ marginBottom: "2rem" }} aria-labelledby="tool-call-filters">
        <h2 id="tool-call-filters" style={{ fontSize: "2rem", marginBottom: "1rem" }}>Filters</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "end" }}>
          <label>
            <span style={{ display: "block", marginBottom: ".35rem" }}>Agent</span>
            <input value={agent} onChange={(event) => setAgent(event.target.value)} placeholder="Agent name or ID" style={filterControlStyle} />
          </label>
          <label>
            <span style={{ display: "block", marginBottom: ".35rem" }}>Tool</span>
            <input value={tool} onChange={(event) => setTool(event.target.value)} placeholder="e.g. issue_refund" style={filterControlStyle} />
          </label>
          <label>
            <span style={{ display: "block", marginBottom: ".35rem" }}>Decision</span>
            <select value={decision} onChange={(event) => setDecision(event.target.value)} style={filterControlStyle}>
              <option value="">All decisions</option>
              <option value="ALLOW">Allow</option>
              <option value="BLOCK">Block</option>
            </select>
          </label>
          <button type="button" onClick={() => { setAgent(""); setTool(""); setDecision(""); }} style={{ ...filterControlStyle, minWidth: "auto", cursor: "pointer" }}>
            Clear
          </button>
        </div>
      </section>

      <section aria-live="polite">
        <h2 style={{ fontSize: "2rem", marginBottom: "1rem" }}>Audit log ({toolCalls.length})</h2>
        {loading ? (
          <p style={{ color: "var(--muted)" }}>Loading tool calls…</p>
        ) : toolCalls.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>No tool calls match these filters.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--line)" }}>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Agent</th>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Tool</th>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Arguments</th>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Decision</th>
                  <th style={{ textAlign: "right", padding: ".65rem" }}>Risk</th>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Time</th>
                  <th style={{ textAlign: "left", padding: ".65rem" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {toolCalls.map((call) => (
                  <tr key={call.id} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: ".65rem" }}>{call.agent_name ?? call.agent_id ?? "Unassigned"}</td>
                    <td style={{ padding: ".65rem" }}><code>{call.tool_name}</code></td>
                    <td style={{ padding: ".65rem", maxWidth: "20rem" }}>
                      <code style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{JSON.stringify(call.arguments)}</code>
                    </td>
                    <td style={{ padding: ".65rem" }}>
                      <span style={{ padding: ".25rem .5rem", borderRadius: ".3rem", color: "white", background: decisionColor(call.decision), fontSize: ".8rem", fontWeight: 700 }}>{call.decision}</span>
                    </td>
                    <td style={{ textAlign: "right", padding: ".65rem" }}>{call.risk_score.toFixed(1)}</td>
                    <td style={{ padding: ".65rem", color: "var(--muted)", whiteSpace: "nowrap" }}>{new Date(call.created_at).toLocaleString()}</td>
                    <td style={{ padding: ".65rem", whiteSpace: "nowrap" }}>
                      <button type="button" onClick={() => setSelectedCall(call)} style={{ cursor: "pointer", marginRight: ".65rem" }}>Inspect</button>
                      {call.decision === "BLOCK" && (
                        <Link href={`/security-events?tool_call_id=${encodeURIComponent(call.id)}`}>Investigate</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedCall && (
        <section role="dialog" aria-modal="true" aria-labelledby="tool-call-detail-title" style={{ marginTop: "2rem", padding: "1.25rem", border: "1px solid var(--line)", borderRadius: ".75rem", background: "var(--panel)" }}>
          <h2 id="tool-call-detail-title" style={{ fontSize: "2rem" }}>Tool Call Details</h2>
          <button type="button" onClick={() => setSelectedCall(null)} style={{ margin: "1rem 0", padding: ".5rem 1rem", cursor: "pointer" }}>Close</button>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(18rem, 1fr))", gap: "1rem" }}>
            <div>
              <p><strong>ID:</strong> {selectedCall.id}</p>
              <p><strong>Request:</strong> {selectedCall.request_id}</p>
              <p><strong>Agent:</strong> {selectedCall.agent_name ?? selectedCall.agent_id ?? "Unassigned"}</p>
              <p><strong>Tool:</strong> {selectedCall.tool_name}</p>
              <p><strong>Decision:</strong> {selectedCall.decision}</p>
              <p><strong>Risk score:</strong> {selectedCall.risk_score.toFixed(2)}</p>
              <p><strong>Duration:</strong> {selectedCall.duration_ms ?? "N/A"} ms</p>
              <p><strong>Created:</strong> {new Date(selectedCall.created_at).toLocaleString()}</p>
              {selectedCall.decision === "BLOCK" && (
                <p><Link href={`/security-events?tool_call_id=${encodeURIComponent(selectedCall.id)}`}>Investigate linked security event</Link></p>
              )}
            </div>
            <div>
              <p><strong>Sanitized arguments</strong></p>
              <pre style={{ padding: ".75rem", overflow: "auto", maxHeight: "18rem", border: "1px solid var(--line)", borderRadius: ".4rem" }}>{formatArguments(selectedCall.arguments)}</pre>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
