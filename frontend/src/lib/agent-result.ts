export type AgentDecision = {
  action: "tool" | "respond";
  tool_name?: string | null;
  arguments: Record<string, unknown>;
  response?: string | null;
};

export type AgentResult = {
  status?: string;
  decision: AgentDecision;
  tool_result: Record<string, unknown> | null;
  provider: string;
  request_id?: string;
};

export type AgentResultPresentation = {
  summary: string;
  toolName: string;
  argumentsText: string;
  toolResultText: string;
};

export function formatStructuredValue(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function presentAgentResult(result: AgentResult): AgentResultPresentation {
  if (result.decision.action === "respond") {
    return {
      summary: result.decision.response ?? "The agent returned an empty response.",
      toolName: "No tool requested",
      argumentsText: "No arguments",
      toolResultText: "No tool was executed for this request.",
    };
  }

  const toolName = result.decision.tool_name ?? "Unknown tool";
  return {
    summary: `The agent selected ${toolName} and the tool execution completed.`,
    toolName,
    argumentsText: formatStructuredValue(result.decision.arguments),
    toolResultText:
      result.tool_result === null
        ? "The tool did not return a result."
        : formatStructuredValue(result.tool_result),
  };
}
