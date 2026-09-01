export type Policy = {
  id: string;
  name: string;
  description: string | null;
  refund_limit: number;
  rate_limit_per_minute: number;
  priority: number;
  is_enabled: boolean;
  updated_at: string;
};

export type ToolPermission = {
  id: string;
  agent_id: string;
  agent_name: string;
  tool_id: string;
  tool_name: string;
  allowed: boolean;
  updated_at: string;
};

export type PolicyAudit = {
  id: string;
  request_id: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  created_at: string;
};

export type PolicyOverview = {
  policies: Policy[];
  permissions: ToolPermission[];
  recent_changes: PolicyAudit[];
};

export function validatePolicyValues(refundLimit: number, rateLimit: number): string[] {
  const errors: string[] = [];
  if (!Number.isFinite(refundLimit) || refundLimit <= 0 || refundLimit > 10_000) {
    errors.push("Refund limit must be greater than 0 and no more than 10,000.");
  }
  if (!Number.isInteger(rateLimit) || rateLimit < 1 || rateLimit > 1_000) {
    errors.push("Rate limit must be a whole number from 1 to 1,000.");
  }
  return errors;
}

export function describeAudit(change: PolicyAudit): string {
  return change.action === "tool_permission_updated"
    ? `Changed ${String(change.after.tool ?? "tool")} permission`
    : "Changed runtime limits";
}
