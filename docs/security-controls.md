# Security Controls

Every model-selected tool action is an untrusted proposal. `ToolGateway`
evaluates it with independent deterministic controls and invokes the registry's
private dispatcher only when no blocking reason exists. An exception in any
control becomes `SECURITY_CONTROL_FAILURE`, so failure cannot silently allow a
tool call.

| Control | Input | Blocking conditions | Primary reason codes |
| --- | --- | --- | --- |
| Tool registry and argument schema | Tool name and arguments | Unknown tool, extra/missing/invalid field, out-of-range value | `UNKNOWN_TOOL`; HTTP 422 argument failure |
| Prompt injection | Original user prompt | Normalized override, guardrail-bypass, or system-prompt request pattern | `PROMPT_INJECTION_DETECTED` |
| Sensitive data | Prompt plus serialized arguments | Two or more sensitive-data indicators in an email action | `SENSITIVE_DATA_EXFILTRATION_DETECTED` |
| Network destination | `fetch_url.url` | Localhost, encoded hostname, or non-global canonical/legacy IP literal | `UNSAFE_NETWORK_DESTINATION` |
| Tool permission | Trusted agent ID and registered tool | Missing/inactive/denied agent-tool grant | `TOOL_NOT_AUTHORIZED` |
| Policy limits | Active stored rules | Refund above configured maximum or request beyond fixed-window rate | `REFUND_LIMIT_EXCEEDED`, `RATE_LIMIT_EXCEEDED` |

## Risk and decision model

Each control returns an allow/block result, stable reason, explanation, and
signal weight. The risk engine deduplicates reason codes, caps the total at 100,
and maps configured thresholds to low, medium, high, or critical. A score
explains severity; it does not override a blocking control. Authorization stays
deny-by-default and deterministic.

## Audit behavior

Successful, blocked, validation-failed, and tool-failed attempts retain a
request ID, tool-call ID, agent ID, status, duration, arguments, result/reason,
and time. Blocking decisions also create linked security events with risk,
reason codes, and explanations. Investigation APIs mask known secret-bearing
argument keys recursively and bound pagination to 200 records.

## Control limitations

Text detectors are transparent heuristics and cannot prove a prompt safe.
Authorization, input validation, side-effect isolation, and outbound controls
remain necessary even if no injection signal fires. The current rate limiter is
single-process, and the demo URL tool never performs a real network request.
See [limitations.md](limitations.md) and [threat-model.md](threat-model.md).
