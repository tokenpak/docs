# Capabilities

A **capability label** is how a TIP component declares what it does. Components
publish labels during capability negotiation and on the `X-TokenPak-Capability`
header; peers use them to decide whether a connection can proceed (see
[Versioning & compatibility](versioning.md)).

- **Machine-readable source of truth:** [`capabilities-v1.json`](https://docs.tokenpak.ai/schemas/tip/capabilities-v1.json)

## Label format

Every label matches `^(tip|ext)\.[a-z0-9._-]+$`:

- **`tip.<name>`** — reserved by TIP-1.0. The catalog of recognized `tip.*`
  labels is defined by the schema; a component publishes a subset of them.
- **`ext.<namespace>.<name>`** — an extension label owned by an implementer.
  Namespace it so it cannot collide with a TIP-reserved label or another
  implementer's extension.

Anything that is neither `tip.*` nor `ext.*` is invalid.

## Capability classes

Each label carries a `class` describing how it behaves:

| Class | Meaning |
|---|---|
| `required` | A core requirement of the profile. |
| `optional` | Used if both peers support it; never required. |
| `profile-specific` | Required only for the named profile(s) in the label's `profiles` list. |
| `local-only` | Must **not** cross the machine boundary — a purely local helper. |
| `passthrough-sensitive` | Subject to the byte-fidelity rule; affects how request bytes are handled. |

## Catalog by profile

The labels below are drawn from the published catalog. Each is `profile-specific`
unless noted.

### `tip-proxy`

| Label | What it asserts |
|---|---|
| `tip.compression.v1` | Runs TIP-1.0 context compression before dispatch, reducing tokens without changing semantic content. |
| `tip.byte-preserved-passthrough` | Preserves exact request-body bytes on passthrough (no re-serialization). `passthrough-sensitive`. Required where billing routing depends on body bytes. |
| `tip.cache.provider-observer` | Reports provider cache hits separately from TokenPak cache hits and never conflates them. |
| `tip.telemetry.wire-side` | Writes one wire-side telemetry row per request to the telemetry store. |
| `tip.routing.fallback-chain` | Applies user-configured routing rules with ordered fallback chains on provider failure. |
| `tip.security.dlp-redaction` | Runs DLP / secret redaction over request bodies before dispatch. |

### `tip-companion`

| Label | What it asserts |
|---|---|
| `tip.preview.local` | Provides local-only preview/simulation (compression preview, cost simulation) that never calls a provider. `local-only`. |
| `tip.companion.prompt-packaging` | Packages prompts client-side before sending. |
| `tip.companion.memory-capsule` | Manages reusable memory capsules for prompt injection. |
| `tip.companion.session-journal` | Maintains a local session journal of prompt-side events. |

### `tip-adapter`

| Label | What it asserts |
|---|---|
| `tip.adapter.client-integration` | Wires a specific client tool (Claude Code, Cursor, Aider, …) to a TIP-proxy. |
| `tip.adapter.framework-bridge` | Exposes TokenPak to a user-space framework (LangChain, LlamaIndex, CrewAI, AutoGen). |

### `tip-plugin`

| Label | What it asserts |
|---|---|
| `tip.plugin.hook-point` | Registers with the plugin system and installs hooks at documented pipeline stages. |

### `tip-dashboard-consumer`

| Label | What it asserts |
|---|---|
| `tip.dashboard.read-only` | Reads the telemetry store and presents derived views; no writes, no business logic beyond aggregation. |
| `tip.alerts.threshold-notifier` | Evaluates user-configured thresholds against telemetry and dispatches notifications. |

### Cross-profile (opt-in)

| Label | Class | What it asserts |
|---|---|---|
| `tip.intent.contract-headers-v1` | `optional` | Respects and forwards the `X-TokenPak-Intent-*` and `X-TokenPak-Contract-*` headers without re-serializing them. Published by `tip-proxy` and `tip-adapter`. |

## Worked example — a capability document

A proxy publishing the subset of `tip.*` labels it actually implements:

```json
{
  "tip_version": "TIP-1.0",
  "labels": [
    {
      "id": "tip.compression.v1",
      "description": "Runs TIP-1.0 context compression before dispatch.",
      "class": "profile-specific",
      "profiles": ["tip-proxy"]
    },
    {
      "id": "tip.byte-preserved-passthrough",
      "description": "Preserves exact request-body byte-identity on passthrough.",
      "class": "passthrough-sensitive",
      "profiles": ["tip-proxy"]
    },
    {
      "id": "tip.cache.provider-observer",
      "description": "Reports provider cache hits separately from proxy cache hits.",
      "class": "profile-specific",
      "profiles": ["tip-proxy"]
    }
  ]
}
```

The same labels, comma-joined, are what this proxy would place on the
`X-TokenPak-Capability` request header:

```
X-TokenPak-Capability: tip.compression.v1,tip.byte-preserved-passthrough,tip.cache.provider-observer
```

## See also

- [Versioning & compatibility](versioning.md) — how `requires_peer_capabilities`
  consumes these labels during negotiation.
- [Profiles & manifests](profiles.md) — where a component lists the capabilities
  it publishes.
- Registry schema: [`capabilities-v1.json`](https://docs.tokenpak.ai/schemas/tip/capabilities-v1.json)
