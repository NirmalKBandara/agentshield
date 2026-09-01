import { describe, expect, it } from "vitest";

import {
  buildSecurityEventsQuery,
  eventReason,
  severityColor,
  type SecurityEvent,
} from "../src/lib/security-events";

const event: SecurityEvent = {
  id: "event-1",
  event_type: "tool_call_blocked",
  severity: "high",
  message: "Tool call was blocked",
  risk_score: 82,
  tool_call_id: null,
  created_at: "2026-08-31T00:00:00Z",
  details: { reason: "Refund exceeds the configured limit" },
};

describe("security event presentation", () => {
  it("builds encoded API filters", () => {
    expect(
      buildSecurityEventsQuery({
        severity: "high",
        eventType: "prompt injection",
        minimumRisk: 50,
        toolCallId: "call-123",
      }),
    ).toBe(
      "?severity=high&event_type=prompt+injection&min_risk_score=50&tool_call_id=call-123",
    );
  });

  it("uses a structured reason and falls back to the message", () => {
    expect(eventReason(event)).toBe("Refund exceeds the configured limit");
    expect(eventReason({ ...event, reason: "Explicit API reason" })).toBe("Explicit API reason");
    expect(eventReason({ ...event, details: {} })).toBe("Tool call was blocked");
  });

  it("provides a stable color for known and unknown severities", () => {
    expect(severityColor("critical")).toBe("#b4233c");
    expect(severityColor("informational")).toBe("#5f7068");
  });
});
