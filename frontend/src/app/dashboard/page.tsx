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
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    async function loadDashboard() {
      setLoading(true);
      setError("");
      try {
        const responses = await Promise.all([
          fetch("/api/dashboard-summary", { signal: controller.signal, cache: "no-store" }),
          fetch("/api/dashboard-events", { signal: controller.signal, cache: "no-store" }),
        ]);
        if (responses.some((response) => !response.ok)) throw new Error("Dashboard data could not be loaded. Try again.");
        const [summaryData, eventsData] = await Promise.all(responses.map((response) => response.json()));
        if (!controller.signal.aborted) {
          setSummary(summaryData as DashboardSummary);
          setEvents(eventsData as RecentEvent[]);
        }
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Dashboard unavailable");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void loadDashboard();
    return () => controller.abort();
  }, [refresh]);

  const blockRate = summary && summary.total_requests > 0
    ? Math.round((summary.blocked_requests / summary.total_requests) * 100) : 0;

  return (
    <main id="main-content" className="app-main" tabIndex={-1}>
      <header className="page-actions">
        <div>
          <p className="eyebrow">Security monitoring</p>
          <h1>Dashboard</h1>
          <p className="page-intro">Review gateway decisions and investigate recent security events.</p>
        </div>
        <button className="secondary-button" onClick={() => setRefresh((value) => value + 1)} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh dashboard"}
        </button>
      </header>
      {loading ? (
        <div className="loading-state" role="status"><span className="loading-state__pulse" aria-hidden="true" /><strong>Loading security overview…</strong></div>
      ) : error ? (
        <div className="error" role="alert"><strong>Dashboard unavailable</strong><p>{error}</p></div>
      ) : summary && (
        <>
          <section aria-labelledby="overview-title">
            <h2 id="overview-title">Security overview</h2>
            <dl className="metric-grid">
              <div className="metric-card metric-card--critical"><dt>Critical events</dt><dd>{summary.critical_events}</dd></div>
              <div className="metric-card metric-card--high"><dt>High-risk events</dt><dd>{summary.high_risk_events}</dd></div>
              <div className="metric-card"><dt>Blocked requests</dt><dd>{summary.blocked_requests}</dd><small>{blockRate}% of total requests</small></div>
              <div className="metric-card"><dt>Total requests</dt><dd>{summary.total_requests}</dd></div>
              <div className="metric-card"><dt>Succeeded requests</dt><dd>{summary.allowed_requests}</dd></div>
              <div className="metric-card"><dt>Most attacked tool</dt><dd>{summary.most_attacked_tool || "None recorded"}</dd></div>
              <div className="metric-card"><dt>Most common attack</dt><dd>{summary.most_common_attack || "None recorded"}</dd></div>
            </dl>
          </section>
          <section aria-labelledby="recent-events-title">
            <div className="page-actions"><h2 id="recent-events-title">Recent security events</h2><Link href="/security-events">View all security events →</Link></div>
            {events.length === 0 ? (
              <div className="empty-state"><strong>No security events recorded</strong><p>Run a request in the <Link href="/playground">Agent Playground</Link> or try a simulation in the <Link href="/red-team">Red Team Lab</Link> to inspect gateway decisions here.</p></div>
            ) : (
              <div className="table-scroll" role="region" aria-label="Recent security events" tabIndex={0}>
                <table className="data-table">
                  <thead><tr><th scope="col">Type</th><th scope="col">Severity</th><th scope="col">Message</th><th scope="col">Risk score</th><th scope="col">Time</th></tr></thead>
                  <tbody>{events.map((event) => (
                    <tr key={event.id}>
                      <td>{event.event_type}</td><td><span className={`severity severity--${event.severity}`}>{event.severity}</span></td>
                      <td>{event.message}</td><td>{event.risk_score.toFixed(1)}</td><td>{new Date(event.created_at).toLocaleString()}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}
