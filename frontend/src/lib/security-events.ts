export interface SecurityEvent {
  id: string;
  event_type: string;
  severity: string;
  message: string;
  reason?: string;
  risk_score: number;
  tool_call_id: string | null;
  created_at: string;
  details: Record<string, unknown>;
}

export interface SecurityEventFilters {
  severity?: string;
  eventType?: string;
  minimumRisk?: number;
}

export function buildSecurityEventsQuery(filters: SecurityEventFilters): string {
  const query = new URLSearchParams();

  if (filters.severity) query.set("severity", filters.severity);
  if (filters.eventType) query.set("event_type", filters.eventType);
  if (filters.minimumRisk !== undefined) {
    query.set("min_risk_score", filters.minimumRisk.toString());
  }

  const value = query.toString();
  return value ? `?${value}` : "";
}

export function eventReason(event: SecurityEvent): string {
  if (typeof event.reason === "string" && event.reason.trim()) return event.reason;
  const reason = event.details.reason;
  return typeof reason === "string" && reason.trim() ? reason : event.message;
}

export function severityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "#b4233c";
    case "high":
      return "#c45d00";
    case "warning":
    case "medium":
      return "#9a6700";
    case "low":
      return "#087f5b";
    default:
      return "#5f7068";
  }
}
