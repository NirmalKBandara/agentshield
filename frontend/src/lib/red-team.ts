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

export function riskLabel(score: number): "Critical" | "High" | "Medium" | "Low" {
  if (score >= 90) return "Critical";
  if (score >= 70) return "High";
  if (score >= 40) return "Medium";
  return "Low";
}
