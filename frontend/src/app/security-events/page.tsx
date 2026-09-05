"use client";

import { useEffect, useState } from "react";
import {
  buildSecurityEventsQuery,
  eventReason,
  SecurityEvent,
} from "@/lib/security-events";

export default function SecurityEventsPage() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [severity, setSeverity] = useState("");
  const [eventType, setEventType] = useState("");
  const [minimumRisk, setMinimumRisk] = useState(0);
  const [toolCallId, setToolCallId] = useState(() =>
    typeof window === "undefined"
      ? ""
      : (new URLSearchParams(window.location.search).get("tool_call_id") ?? ""),
  );
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function loadEvents() {
      setLoading(true);
      setError("");
      try {
        const query = buildSecurityEventsQuery({
          severity,
          eventType,
          minimumRisk: minimumRisk || undefined,
          toolCallId: toolCallId || undefined,
        });
        const url = `/api/security-events${query}`;
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error("Failed to load events");
        const data = (await response.json()) as SecurityEvent[];
        if (!controller.signal.aborted) setEvents(data);
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Error loading events");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void loadEvents();
    return () => controller.abort();
  }, [severity, eventType, minimumRisk, toolCallId, refresh]);


  return (
    <main id="main-content" className="app-main" tabIndex={-1}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>Security Events</h1>
      </header>

      {error && (
        <div className="error" role="alert">
          <p>{error}</p><button className="secondary-button" disabled={loading} onClick={() => setRefresh((value) => value + 1)}>Retry loading</button>
        </div>
      )}

      {toolCallId && (
        <p style={{ padding: ".75rem", border: "1px solid var(--line)", borderRadius: ".4rem" }}>
          Showing events linked to tool call <code>{toolCallId}</code>.{" "}
          <button type="button" onClick={() => setToolCallId("")}>Show all events</button>
        </p>
      )}

      <section style={{ marginBottom: "2rem" }} aria-labelledby="event-filters">
        <h2 id="event-filters" style={{ fontSize: "2rem", marginBottom: "1rem" }}>Filters</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "end" }}>
          <label>
            <span style={{ display: "block", marginBottom: ".35rem" }}>Event type</span>
            <input
              value={eventType}
              onChange={(event) => setEventType(event.target.value)}
              placeholder="e.g. tool_call_blocked"
              style={{ padding: ".55rem", minWidth: "14rem" }}
            />
          </label>
          <label>
            <span style={{ display: "block", marginBottom: ".35rem" }}>Minimum risk</span>
            <select
              value={minimumRisk}
              onChange={(event) => setMinimumRisk(Number(event.target.value))}
            >
              <option value={0}>Any score</option>
              <option value={25}>25+</option>
              <option value={50}>50+</option>
              <option value={75}>75+</option>
            </select>
          </label>
        </div>
        <div className="examples" role="group" aria-label="Filter by severity">
          {["", "critical", "high", "medium", "warning", "low"].map((level) => (
            <button key={level} type="button" aria-pressed={severity === level} onClick={() => setSeverity(level)}>
              {level ? level.charAt(0).toUpperCase() + level.slice(1) : "All severities"}
            </button>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Events ({events.length})</h2>
        {loading ? <p className="loading-state" role="status">Loading security events…</p> : error ? null : events.length === 0 ? (
          <p className="empty-state">No security events match these filters. Try another severity or clear the event type and minimum risk.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #ddd" }}>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Type</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Severity</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Reason</th>
                  <th style={{ textAlign: "right", padding: "0.5rem" }}>Risk</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Time</th>
                  <th style={{ textAlign: "left", padding: "0.5rem" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "0.5rem" }}>
                      <code style={{ fontSize: "0.85rem" }}>{event.event_type}</code>
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <span className={`severity severity--${event.severity}`}>{event.severity}</span>
                    </td>
                    <td style={{ padding: "0.5rem" }}>{eventReason(event)}</td>
                    <td style={{ textAlign: "right", padding: "0.5rem" }}>
                      {event.risk_score.toFixed(1)}
                    </td>
                    <td style={{ padding: "0.5rem", fontSize: "0.875rem", color: "#999" }}>
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <button
                        onClick={() => setSelectedEvent(event)}
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

      {selectedEvent && (
        <section
          aria-labelledby="event-detail-title"
          style={{ marginTop: "2rem", padding: "1rem", backgroundColor: "var(--panel)", border: "1px solid var(--line)" }}
        >
          <h2 id="event-detail-title">Event Details</h2>
          <button
            onClick={() => setSelectedEvent(null)}
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
          <div>
            <p>
              <strong>ID:</strong> {selectedEvent.id}
            </p>
            <p>
              <strong>Type:</strong> {selectedEvent.event_type}
            </p>
            <p>
              <strong>Severity:</strong> {selectedEvent.severity}
            </p>
            <p>
              <strong>Message:</strong> {selectedEvent.message}
            </p>
            <p>
              <strong>Reason:</strong> {eventReason(selectedEvent)}
            </p>
            <p>
              <strong>Risk Score:</strong> {selectedEvent.risk_score.toFixed(2)}
            </p>
            <p>
              <strong>Created:</strong> {new Date(selectedEvent.created_at).toLocaleString()}
            </p>
            {selectedEvent.tool_call_id && (
              <p>
                <strong>Tool Call ID:</strong> {selectedEvent.tool_call_id}
              </p>
            )}
            <p>
              <strong>Details:</strong>
            </p>
            <pre
              style={{
                backgroundColor: "var(--panel)",
                padding: "0.5rem",
                borderRadius: "0.25rem",
                overflow: "auto",
              }}
            >
              {JSON.stringify(selectedEvent.details, null, 2)}
            </pre>
          </div>
        </section>
      )}
    </main>
  );
}
