import { describe, expect, it } from "vitest";

import {
  buildToolCallsQuery,
  decisionColor,
  formatArguments,
} from "../src/lib/tool-calls";

describe("tool call presentation", () => {
  it("builds encoded API filters", () => {
    expect(
      buildToolCallsQuery({
        agent: "support agent",
        tool: "issue/refund",
        decision: "BLOCK",
      }),
    ).toBe("?agent=support+agent&tool_name=issue%2Frefund&decision=BLOCK");
  });

  it("omits empty filters", () => {
    expect(buildToolCallsQuery({ agent: "  ", tool: "", decision: "" })).toBe("");
  });

  it("formats sanitized arguments for inspection", () => {
    expect(formatArguments({ email: "[REDACTED]", amount: 50 })).toContain(
      '"email": "[REDACTED]"',
    );
  });

  it("provides stable decision colors", () => {
    expect(decisionColor("ALLOW")).toBe("#087f5b");
    expect(decisionColor("BLOCK")).toBe("#b4233c");
    expect(decisionColor("PENDING")).toBe("#5f7068");
  });
});
