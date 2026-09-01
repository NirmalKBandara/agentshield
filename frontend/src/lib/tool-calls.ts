export type ToolCallDecision = "ALLOW" | "BLOCK" | "ERROR" | "PENDING";

export interface ToolCall {
  id: string;
  request_id: string;
  agent_id: string | null;
  agent_name: string | null;
  tool_name: string;
  status: string;
  decision: ToolCallDecision;
  risk_score: number;
  duration_ms: number | null;
  created_at: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
  security_event_id: string | null;
}

export interface ToolCallFilters {
  agent?: string;
  tool?: string;
  decision?: string;
}

export function buildToolCallsQuery(filters: ToolCallFilters): string {
  const query = new URLSearchParams();

  if (filters.agent?.trim()) query.set("agent", filters.agent.trim());
  if (filters.tool?.trim()) query.set("tool_name", filters.tool.trim());
  if (filters.decision) query.set("decision", filters.decision);

  const value = query.toString();
  return value ? `?${value}` : "";
}

export function decisionColor(decision: ToolCallDecision): string {
  switch (decision) {
    case "ALLOW":
      return "#087f5b";
    case "BLOCK":
      return "#b4233c";
    case "ERROR":
      return "#c45d00";
    default:
      return "#5f7068";
  }
}

export function formatArguments(argumentsValue: Record<string, unknown>): string {
  return JSON.stringify(argumentsValue, null, 2);
}
