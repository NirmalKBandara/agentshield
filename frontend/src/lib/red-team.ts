export type RedTeamScenario = {
  id: string;
  name: string;
  category: string;
  description: string;
  payload: Record<string, unknown>;
  requested_action: Record<string, unknown>;
};

export type RedTeamRun = {
  security_event_id: string;
  request_id: string;
  scenario_id: string;
  payload: Record<string, unknown>;
  requested_action: Record<string, unknown>;
  triggered_controls: string[];
  reason: string;
  score: number;
  risk_level?: "critical" | "high" | "medium" | "low";
  decision: "block";
  created_at: string;
};

export function formatControl(control: string): string {
  return control
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function riskLabel(score: number, level?: RedTeamRun["risk_level"]): "Critical" | "High" | "Medium" | "Low" {
  if (level === "critical") return "Critical";
  if (level === "high") return "High";
  if (level === "medium") return "Medium";
  if (level === "low") return "Low";
  if (score >= 80) return "Critical";
  if (score >= 60) return "High";
  if (score >= 30) return "Medium";
  return "Low";
}
