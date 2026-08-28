import { describe, expect, it } from "vitest";

import { presentAgentResult } from "../src/lib/agent-result";

describe("presentAgentResult", () => {
  it("presents a tool decision as separate, readable fields", () => {
    const presentation = presentAgentResult({
      decision: { action: "tool", tool_name: "get_customer", arguments: { customer_id: "1002" } },
      tool_result: { found: true, customer: { name: "Morgan Silva" } },
      provider: "rules",
    });

    expect(presentation.toolName).toBe("get_customer");
    expect(presentation.argumentsText).toContain('\"customer_id\": \"1002\"');
    expect(presentation.toolResultText).toContain('\"found\": true');
    expect(presentation.summary).toContain("execution completed");
  });

  it("makes a direct response and absence of a tool explicit", () => {
    const presentation = presentAgentResult({
      decision: { action: "respond", arguments: {}, response: "I can help with one of the available demo tools." },
      tool_result: null,
      provider: "rules",
    });

    expect(presentation.summary).toBe("I can help with one of the available demo tools.");
    expect(presentation.toolName).toBe("No tool requested");
    expect(presentation.argumentsText).toBe("No arguments");
    expect(presentation.toolResultText).toBe("No tool was executed for this request.");
  });
});
