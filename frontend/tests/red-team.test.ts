import { describe, expect, it } from "vitest";

import { formatControl, riskLabel } from "../src/lib/red-team";

describe("red-team result presentation", () => {
  it("formats gateway control identifiers for people", () => {
    expect(formatControl("prompt-injection-detector")).toBe("Prompt Injection Detector");
    expect(formatControl("policy-limits")).toBe("Policy Limits");
  });

  it("uses the backend risk level when policy thresholds differ", () => {
    expect(riskLabel(80, "medium")).toBe("Medium");
    expect(riskLabel(20, "high")).toBe("High");
  });

  it("maps bounded scores to risk labels", () => {
    expect(riskLabel(100)).toBe("Critical");
    expect(riskLabel(90)).toBe("Critical");
    expect(riskLabel(80)).toBe("Critical");
    expect(riskLabel(79)).toBe("High");
    expect(riskLabel(60)).toBe("High");
    expect(riskLabel(59)).toBe("Medium");
    expect(riskLabel(30)).toBe("Medium");
    expect(riskLabel(29)).toBe("Low");
    expect(riskLabel(65)).toBe("High");
    expect(riskLabel(0)).toBe("Low");
  });
});
