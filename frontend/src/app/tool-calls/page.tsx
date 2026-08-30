"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface ToolCall {
  id: string;
  request_id: string;
  agent_id: string | null;
  tool_name: string;
  status: string;
  duration_ms: number | null;
  created_at: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
}

export default function ToolCallsPage() {
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [selectedCall, setSelectedCall] = useState<ToolCall | null>(null);

  useEffect(() => {
    async function loadToolCalls() {
      try {
        const url = status ? `/api/tool-calls?status=${status}` : "/api/tool-calls";
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to load tool calls");
        const data = (await response.json()) as ToolCall[];
        setToolCalls(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading tool calls");
      } finally {
        setLoading(false);
      }
    }
    void loadToolCalls();
  }, [status]);

  if (loading) {
    return (
      <main style={{ padding: "2rem" }}>
        <p>Loading tool calls...</p>
      </main>
    );
  }

  const statusColor = (s: string) => {
    switch (s) {
      case "succeeded":
        return "#28a745";
      case "blocked":
        return "#dc3545";
      case "failed":
        return "#ff9800";
      default:
        return "#999";
    }
  };

  return (
    <main style={{ padding: "2rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>Tool Calls</h1>
        <nav style={{ marginTop: "1rem" }}>
          <Link href="/" style={{ marginRight: "1rem" }}>
            Home
          </Link>
          <Link href="/dashboard" style={{ marginRight: "1rem" }}>
            Dashboard
          </Link>
          <Link href="/playground" style={{ marginRight: "1rem" }}>
            Playground
          </Link>
          <Link href="/security-events">Security Events</Link>
        </nav>
      </header>

      {error && (
        <div style={{ padding: "1rem", backgroundColor: "#ffebee", borderRadius: "0.25rem" }}>
          <p>Error: {error}</p>
        </div>
      )}

      <section style={{ marginBottom: "2rem" }}>
        <h2>Filter by Status</h2>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            onClick={() => setStatus(null)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: !status ? "#2196f3" : "#ddd",
              color: !status ? "white" : "black",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
            }}
          >
            All
          </button>
          <button
            onClick={() => setStatus("succeeded")}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: status === "succeeded" ? "#28a745" : "#ddd",
              color: status === "succeeded" ? "white" : "black",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
            }}
          >
            Succeeded
          </button>
          <button
            onClick={() => setStatus("blocked")}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: status === "blocked" ? "#dc3545" : "#ddd",
              color: status === "blocked" ? "white" : "black",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
            }}
          >
            Blocked
          </button>
          <button
            onClick={() => setStatus("failed")}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: status === "failed" ? "#ff9800" : "#ddd",
              color: status === "failed" ? "white" : "black",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
            }}
          >
            Failed
          </button>
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Tool Calls ({toolCalls.length})</h2>
        {toolCalls.length === 0 ? (
          <p style={{ color: "#999" }}>No tool calls found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #ddd" }}>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Tool</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Status</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Request ID</th>
                  <th style={{ textAlign: "right", padding: "0.5rem" }}>Duration (ms)</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Time</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {toolCalls.map((call) => (
                  <tr key={call.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "0.5rem" }}>
                      <code style={{ fontSize: "0.85rem" }}>{call.tool_name}</code>
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <span
                        style={{
                          padding: "0.25rem 0.5rem",
                          borderRadius: "0.25rem",
                          backgroundColor: statusColor(call.status),
                          color: "white",
                          fontSize: "0.875rem",
                        }}
                      >
                        {call.status}
                      </span>
                    </td>
                    <td style={{ padding: "0.5rem", fontSize: "0.875rem", fontFamily: "monospace" }}>
                      {call.request_id.substring(0, 8)}...
                    </td>
                    <td style={{ textAlign: "right", padding: "0.5rem" }}>
                      {call.duration_ms ?? "—"}
                    </td>
                    <td style={{ padding: "0.5rem", fontSize: "0.875rem", color: "#999" }}>
                      {new Date(call.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <button
                        onClick={() => setSelectedCall(call)}
                        style={{
                          padding: "0.25rem 0.5rem",
                          backgroundColor: "#2196f3",
                          color: "white",
                          border: "none",
                          borderRadius: "0.25rem",
                          cursor: "pointer",
                          fontSize: "0.875rem",
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedCall && (
        <section style={{ marginTop: "2rem", padding: "1rem", backgroundColor: "#f5f5f5" }}>
          <h2>Tool Call Details</h2>
          <button
            onClick={() => setSelectedCall(null)}
            style={{
              marginBottom: "1rem",
              padding: "0.5rem 1rem",
              backgroundColor: "#ddd",
              border: "none",
              borderRadius: "0.25rem",
              cursor: "pointer",
            }}
          >
            Close
          </button>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <p>
                <strong>ID:</strong> {selectedCall.id}
              </p>
              <p>
                <strong>Tool:</strong> {selectedCall.tool_name}
              </p>
              <p>
                <strong>Status:</strong> {selectedCall.status}
              </p>
              <p>
                <strong>Request ID:</strong> {selectedCall.request_id}
              </p>
              {selectedCall.agent_id && (
                <p>
                  <strong>Agent ID:</strong> {selectedCall.agent_id}
                </p>
              )}
              <p>
                <strong>Duration:</strong> {selectedCall.duration_ms ?? "N/A"} ms
              </p>
              <p>
                <strong>Created:</strong> {new Date(selectedCall.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p>
                <strong>Arguments:</strong>
              </p>
              <pre
                style={{
                  backgroundColor: "#fff",
                  padding: "0.5rem",
                  borderRadius: "0.25rem",
                  overflow: "auto",
                  maxHeight: "200px",
                }}
              >
                {JSON.stringify(selectedCall.arguments, null, 2)}
              </pre>
            </div>
          </div>
          {selectedCall.result && (
            <div style={{ marginTop: "1rem" }}>
              <p>
                <strong>Result:</strong>
              </p>
              <pre
                style={{
                  backgroundColor: "#fff",
                  padding: "0.5rem",
                  borderRadius: "0.25rem",
                  overflow: "auto",
                  maxHeight: "300px",
                }}
              >
                {JSON.stringify(selectedCall.result, null, 2)}
              </pre>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
