# Request/response metadata

Where [wire headers](wire-headers.md) ride on the HTTP envelope, the **metadata
object** carries the same kind of runtime information in-band — attached to a
request and its response so a component can route, record, and reason about a
call without re-parsing headers.

- **Machine-readable source of truth:** [`metadata-v1.json`](https://docs.tokenpak.ai/schemas/tip/metadata-v1.json)

The schema is **closed** (`additionalProperties: false`): every top-level field
below is defined by TIP-1.0. Component-specific data goes under the namespaced
`ext` object, never as a new top-level key.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `request_id` | string | Correlation id; matches the `X-TokenPak-Request-Id` header. |
| `tip_version` | `TIP-<n>.<n>` | TIP version for this request; matches `X-TokenPak-TIP-Version`. |
| `profile` | string | The emitter's profile (`tip-proxy`, `tip-companion`, `tip-adapter`, `tip-plugin`, `tip-dashboard-consumer`). |
| `provider` | string | Canonical outbound provider name (`anthropic`, `openai`, `google`, `ollama`, …). Unknown providers are allowed and reported as `unknown` rather than guessed. |
| `model` | string | Model identifier within the provider (e.g. `claude-opus-4-7`, `gpt-5-codex`). |
| `client` | string | The client tool the user is running (`claude-code`, `cursor`, `aider`, `cline`, `continue`, `codex`, `custom-sdk`, …). |
| `session_id` | string | Client-session identifier when available; used for session-scoped state. |
| `capabilities_negotiated` | string[] | Capability labels negotiated with the peer (the capability intersection). Control-plane metadata — data-plane requests do not renegotiate. |
| `ext` | object | Namespaced extension fields. Core fields must not be shadowed here. |

All fields are optional, but a value that *is* present must agree with its header
counterpart — `request_id` with `X-TokenPak-Request-Id`, `tip_version` with
`X-TokenPak-TIP-Version`, and so on.

## Worked example

Metadata attached to a request that a proxy is about to dispatch to Anthropic on
behalf of Claude Code:

```json
{
  "request_id": "018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2",
  "tip_version": "TIP-1.0",
  "profile": "tip-proxy",
  "provider": "anthropic",
  "model": "claude-opus-4-7",
  "client": "claude-code",
  "session_id": "sess-2f9c1a",
  "capabilities_negotiated": [
    "tip.compression.v1",
    "tip.byte-preserved-passthrough"
  ]
}
```

### Honest `unknown` over a guess

When the outbound provider cannot be resolved (for example a user-configured
endpoint the component does not recognize), report `unknown` rather than
inferring a brand:

```json
{
  "request_id": "018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2",
  "tip_version": "TIP-1.0",
  "profile": "tip-proxy",
  "provider": "unknown",
  "client": "custom-sdk"
}
```

### Using `ext` for extension data

A component that needs to carry its own field does so under `ext`, namespaced so
it cannot collide with a future core field:

```json
{
  "request_id": "018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2",
  "tip_version": "TIP-1.0",
  "profile": "tip-adapter",
  "ext": {
    "acme": {
      "route_hint": "low-latency-pool"
    }
  }
}
```

## See also

- [Wire headers](wire-headers.md) — the header counterparts of these fields.
- [Capabilities](capabilities.md) — the source of `capabilities_negotiated`.
- Registry schema: [`metadata-v1.json`](https://docs.tokenpak.ai/schemas/tip/metadata-v1.json)
