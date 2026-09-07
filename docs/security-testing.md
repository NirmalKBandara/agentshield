# Security Testing Record

Day 24 added adversarial tests at the HTTP, gateway, text-normalization, and URL
boundaries. The suite covers malformed JSON, missing and oversized prompts,
unknown tools, invalid/missing identifiers, log-injection headers, prompt and
PII obfuscation, rate-limit behavior, and SSRF representations.

## Discovered issue and fix

The initial network-destination control recognized canonical IP literals and a
single-integer decimal address, but common URL clients can also interpret
hexadecimal (`0x7f000001`), octal (`0177.0.0.1`), and shortened (`127.1`)
hostnames as `127.0.0.1`. Those forms could bypass the string-to-IP conversion.

The control now parses the legacy one-to-four-component IPv4 grammar, blocks
non-global IP literals, rejects percent-encoded hostnames, handles a trailing
root dot on `localhost`, and retains fail-closed behavior for control errors.
Tests also verify IPv4-mapped IPv6 loopback.

Prompt and sensitive-data checks now strip Unicode formatting controls after
NFKC normalization, closing a zero-width-character bypass without trusting the
model to recognize the attack.

## Test matrix

| Area | Representative cases | Expected result |
| --- | --- | --- |
| JSON/API | Truncated JSON, absent prompt, prompt over 4,000 characters | HTTP 422 with request correlation; no tool call |
| Tool boundary | Unknown tool and invalid/oversized tool arguments | Deny before private dispatch |
| Identifiers/logging | Missing, malformed, and CRLF request IDs | Generate safe UUID; never reflect injected value |
| SSRF | Decimal, hex, octal, short IPv4, mapped IPv6, encoded host, localhost root-dot | Block as unsafe destination |
| Prompt injection | Case/spacing variants, compatibility forms, zero-width separator | Block with stable reason code |
| Sensitive data | Multiple indicators across prompt and arguments with obfuscation | Block outbound email action |
| Bypass safety | Benign security wording and a single PII term | Allow to avoid the tested false positives |
| Rate limit | Request at limit and first request over limit | Allow boundary, then block excess |

The tools remain simulations. Before enabling real outbound HTTP, add DNS
resolution and redirect revalidation plus network-layer egress restrictions.
