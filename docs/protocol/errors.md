# Errors

Every TIP-compatible surface emits errors in one shape: the **TIP error
envelope**. Bare, unstructured error bodies are not conformant — an error must be
machine-readable, name its cause, and point at a next step.

- **Machine-readable source of truth:** [`error-v1.json`](https://docs.tokenpak.ai/schemas/tip/error-v1.json)

The envelope is **closed** (`additionalProperties: false`). `code` and `message`
are required; everything else is contextual.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `code` | string | **Required.** Canonical TIP error code (see the catalog below). Implementations may emit `ext.*` codes for their own error classes but must not collide with TIP-reserved codes. |
| `message` | string | **Required.** Human-readable message. It must name the cause **and** the next step. |
| `tip_version` | `TIP-<n>.<n>` | Emitter's TIP version; present on cross-version error scenarios. |
| `profile` | string | Emitter profile. |
| `request_id` | string | Correlates with `X-TokenPak-Request-Id` when the error is tied to a specific request. |
| `details` | object | Optional structured debugging context. **Must not contain credential material.** |
| `retry_after_ms` | integer ≥ 0 | Backoff hint; present on rate-limit and transient-provider-failure codes. |

## Error code catalog

TIP-1.0 reserves the following codes. They are namespaced by area so a consumer
can branch on the prefix.

| Area | Codes |
|---|---|
| **Auth** | `tip.auth.missing-credentials`, `tip.auth.invalid-credentials`, `tip.auth.refresh-failed` |
| **Policy** | `tip.policy.budget-exceeded`, `tip.policy.rate-limited`, `tip.policy.dlp-redaction-required` |
| **Routing** | `tip.routing.no-provider-available`, `tip.routing.all-providers-down` |
| **Compression** | `tip.compression.strategy-unknown` |
| **Cache** | `tip.cache.write-failed` |
| **Transport** | `tip.transport.connection-lost`, `tip.transport.handshake-failed` |
| **Capability** | `tip.capability.missing-required`, `tip.capability.version-mismatch` |
| **Manifest** | `tip.manifest.invalid`, `tip.manifest.missing-required-field` |
| **Protocol** | `tip.protocol.malformed-frame`, `tip.protocol.unknown-method` |
| **Internal** | `tip.internal.unexpected-error` |

Extension codes use the `ext.<namespace>.<name>` form and must not shadow a
reserved code.

## Worked examples

### A rate-limit error with a backoff hint

```json
{
  "code": "tip.policy.rate-limited",
  "message": "Request rejected: per-minute budget of 60 requests reached. Retry after the window resets or raise the limit in your routing config.",
  "tip_version": "TIP-1.0",
  "profile": "tip-proxy",
  "request_id": "018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2",
  "retry_after_ms": 4200
}
```

### A failed capability negotiation

The error a proxy returns when a peer requires a capability it does not publish
(see [Versioning & compatibility](versioning.md)):

```json
{
  "code": "tip.capability.missing-required",
  "message": "Connection refused: peer requires 'tip.byte-preserved-passthrough', which this proxy does not publish. Enable byte-preserved passthrough or connect a proxy that supports it.",
  "tip_version": "TIP-1.0",
  "profile": "tip-proxy",
  "details": {
    "required": ["tip.byte-preserved-passthrough"],
    "published": ["tip.compression.v1"]
  }
}
```

Note the `details` object carries the diagnostic context — required vs. published
labels — but **no credential material**. That rule is absolute: an error may
explain a failure without ever echoing a secret.

## How errors land in telemetry

When a request fails, its [telemetry row](telemetry.md) records the same `code`
in its `error_code` field and the matching HTTP-style `status`. The envelope and
the telemetry row are two views of the same failure, correlated by `request_id`.

## See also

- [Telemetry](telemetry.md) — where `error_code` is recorded.
- [Versioning & compatibility](versioning.md) — the source of the
  `tip.capability.*` codes.
- Registry schema: [`error-v1.json`](https://docs.tokenpak.ai/schemas/tip/error-v1.json)
