"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface DashboardSummary {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  high_risk_events: number;
  critical_events: number;
  most_attacked_tool: string | null;
  most_common_attack: string | null;
}

interface RecentEvent {
  id: string;
  event_type: string;
  severity: string;
  message: string;
  risk_score: number;
  created_at: string;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryRes, eventsRes] = await Promise.all([
          fetch("/api/dashboard-summary"),
          fetch("/api/dashboard-events"),
        ]);
        if (!summaryRes.ok || !eventsRes.ok) throw new Error("Failed to load dashboard");
        const summaryData = (await summaryRes.json()) as DashboardSummary;
        const eventsData = (await eventsRes.json()) as RecentEvent[];
        setSummary(summaryData);
        setEvents(eventsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading dashboard");
      } finally {
        setLoading(false);
      }
    }
    void loadDashboard();
  }, []);

  if (loading) {
    return (
      <main>
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <p>Loading dashboard...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <div style={{ padding: "2rem", color: "red" }}>
          <p>Error: {error}</p>
        </div>
      </main>
    );
  }

  const blockRate =
    summary && summary.total_requests > 0
      ? Math.round((summary.blocked_requests / summary.total_requests) * 100)
      : 0;

  return (
    <main style={{ padding: "2rem" }}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>AgentShield Dashboard</h1>
        <nav style={{ marginTop: "1rem" }}>
          <Link href="/playground" style={{ marginRight: "1rem" }}>
            Playground
          </Link>
          <Link href="/security-events" style={{ marginRight: "1rem" }}>
            Security Events
          </Link>
          <Link href="/tool-calls">Tool Calls</Link>
        </nav>
      </header>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Security Overview</h2>
        {summary && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>Total Requests</div>
              <div style={{ fontSize: "2rem", fontWeight: "bold" }}>
                {summary.total_requests}
              </div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>Allowed</div>
              <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#28a745" }}>
                {summary.allowed_requests}
              </div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>Blocked</div>
              <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#dc3545" }}>
                {summary.blocked_requests}
              </div>
              <div style={{ fontSize: "0.875rem", color: "#999" }}>({blockRate}% block rate)</div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>High Risk Events</div>
              <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#ff9800" }}>
                {summary.high_risk_events}
              </div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>Critical Events</div>
              <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#dc3545" }}>
                {summary.critical_events}
              </div>
            </div>
            <div style={{ border: "1px solid #ccc", padding: "1rem" }}>
              <div style={{ fontSize: "0.875rem", color: "#666" }}>Most Attacked Tool</div>
              <div style={{ fontSize: "1.25rem", fontWeight: "bold" }}>
                {summary.most_attacked_tool || "N/A"}
              </div>
            </div>
          </div>
        )}
      </section>

      <section>
        <h2>Recent Security Events</h2>
        {events.length === 0 ? (
          <p style={{ color: "#999" }}>No security events yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #ddd" }}>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Type</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Severity</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Message</th>
                  <th style={{ textAlign: "right", padding: "0.5rem" }}>Risk Score</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Time</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "0.5rem" }}>{event.event_type}</td>
                    <td style={{ padding: "0.5rem" }}>
                      <span
                        style={{
                          padding: "0.25rem 0.5rem",
                          borderRadius: "0.25rem",
                          backgroundColor:
                            event.severity === "critical"
                              ? "#dc3545"
                              : event.severity === "high"
                                ? "#ff9800"
                                : "#ffc107",
                          color: "white",
                          fontSize: "0.875rem",
                        }}
                      >
                        {event.severity}
                      </span>
                    </td>
                    <td style={{ padding: "0.5rem" }}>{event.message}</td>
                    <td style={{ textAlign: "right", padding: "0.5rem" }}>
                      {event.risk_score.toFixed(1)}
                    </td>
                    <td style={{ padding: "0.5rem", fontSize: "0.875rem", color: "#999" }}>
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
