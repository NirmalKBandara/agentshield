import { describe, expect, it } from "vitest";

import { formatControl, riskLabel } from "../src/lib/red-team";

describe("red-team result presentation", () => {
  it("formats gateway control identifiers for people", () => {
    expect(formatControl("prompt-injection-detector")).toBe("Prompt Injection Detector");
    expect(formatControl("policy-limits")).toBe("Policy Limits");
  });

  it("maps bounded scores to risk labels", () => {
    expect(riskLabel(100)).toBe("Critical");
    expect(riskLabel(90)).toBe("Critical");
    expect(riskLabel(80)).toBe("High");
    expect(riskLabel(65)).toBe("Medium");
    expect(riskLabel(0)).toBe("Low");
  });
});
