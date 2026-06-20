# Stateful Provider APIs

TokenPak is optimized for request/response provider APIs. Some provider APIs
also expose server-side state, such as conversation IDs, response chaining,
uploaded file references, hosted tools, assistants, threads, runs, provider
memory, batch lifecycle IDs, and real-time sessions.

TokenPak handles these surfaces with explicit support states instead of silent
best-effort behavior.

## Support States

| State | Meaning |
| --- | --- |
| `supported` | TokenPak understands the lifecycle and provides tested product behavior for it. |
| `passed_through` | TokenPak preserves provider state identifiers without owning their lifecycle. |
| `managed` | TokenPak owns additional lifecycle state with documented retention and recovery. |
| `explicitly_unsupported` | TokenPak rejects the surface with a typed error and remediation. |
| `deprecated_compatibility_only` | TokenPak keeps legacy compatibility without extending support. |

## Initial Surface Policy

| Surface | Current support state | Notes |
| --- | --- | --- |
| Provider response IDs | `passed_through` | IDs are preserved; TokenPak does not chain responses for the caller. |
| Provider conversation IDs | `passed_through` | IDs are preserved; provider-side conversation lifecycle remains provider-owned. |
| Provider file IDs | `passed_through` | Opaque file references are preserved. File upload endpoints are not mediated by TokenPak in this scope. |
| Provider hosted tools | `passed_through` | Hosted tool request and response bytes are forwarded; TokenPak does not mediate the hosted runtime. |
| Provider assistants, threads, and runs | `deprecated_compatibility_only` | Legacy wire compatibility is preserved where possible; new work should prefer current provider APIs. |
| Provider-managed conversation memory | `explicitly_unsupported` | TokenPak does not synchronize local PAK memory with provider-managed memory. |
| Provider batch lifecycle IDs | `passed_through` | Batch IDs are preserved; batch lifecycle management is not implemented here. |
| Real-time session IDs | `explicitly_unsupported` | Real-time lifecycle support is a separate future scope. |

## Local PAK Memory and Provider-Managed State

TokenPak local PAK memory is operator-controlled and remains on the operator's
machine. Provider-managed state (conversations, threads, hosted memory) lives in
the provider's infrastructure. These are separate systems with separate
retention, access, and privacy postures. TokenPak does not synchronize between
them.

Use local PAK memory when you want TokenPak-managed context that stays under
local control. Use provider-managed state only when you intentionally want the
provider to own that state lifecycle.

## Unsupported Stateful APIs

When a stateful provider surface is explicitly unsupported, TokenPak returns a
typed error instead of silently forwarding or pretending to manage the lifecycle.
The error uses `tokenpak_error_type: stateful_api_unsupported` and includes:

- `surface`: the provider stateful surface that was rejected
- `support_state`: `explicitly_unsupported`
- `remediation`: a short next step or safer alternative
- `registry_link`: the registry entry for the surface policy

Unsupported stateful API requests return HTTP 422 when TokenPak can parse the
request body, or HTTP 400 when it cannot.
