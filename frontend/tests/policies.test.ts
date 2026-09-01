import { describe, expect, it } from "vitest";

import { describeAudit, validatePolicyValues } from "../src/lib/policies";

describe("policy presentation", () => {
  it("accepts bounded refund and integer rate limits", () => {
    expect(validatePolicyValues(250.5, 60)).toEqual([]);
  });

  it("rejects unsafe or malformed limits", () => {
    expect(validatePolicyValues(0, 1.5)).toEqual([
      "Refund limit must be greater than 0 and no more than 10,000.",
      "Rate limit must be a whole number from 1 to 1,000.",
    ]);
    expect(validatePolicyValues(Number.NaN, 1001)).toHaveLength(2);
  });

  it("describes permission and limits audit entries", () => {
    const base = {
      id: "audit-id",
      request_id: "request-id",
      actor: "dashboard-user",
      resource_type: "policy",
      resource_id: "resource-id",
      before: {},
      created_at: "2026-09-01T00:00:00Z",
    };
    expect(describeAudit({ ...base, action: "policy_limits_updated", after: {} })).toBe(
      "Changed runtime limits",
    );
    expect(
      describeAudit({
        ...base,
        action: "tool_permission_updated",
        after: { tool: "send_email" },
      }),
    ).toBe("Changed send_email permission");
  });
});
