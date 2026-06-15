# Profiles & manifests

A TIP component ships a **manifest** — a JSON document declaring its identity,
the capabilities it publishes, and the [compatibility](versioning.md) block peers
negotiate against. There are four manifest schemas, one per component kind.

| Manifest | Schema | Describes |
|---|---|---|
| Client profile | [`client-profile-v1.json`](https://docs.tokenpak.ai/schemas/manifests/client-profile-v1.json) | An inbound client kind (CLI, TUI, IDE, API, …). |
| Provider profile | [`provider-profile-v1.json`](https://docs.tokenpak.ai/schemas/manifests/provider-profile-v1.json) | An outbound provider (Anthropic, OpenAI, Google, Ollama, …). |
| Adapter | [`adapter-v1.json`](https://docs.tokenpak.ai/schemas/manifests/adapter-v1.json) | A component wiring a client or framework to a proxy. |
| Plugin | [`plugin-v1.json`](https://docs.tokenpak.ai/schemas/manifests/plugin-v1.json) | A component installing hooks at pipeline stages. |

## Shared manifest fields

Every manifest carries the same identity core:

| Field | Meaning |
|---|---|
| `tip_version` | TIP version the manifest targets (`TIP-1.0`). |
| `id` | Lowercase, hyphen-separated identifier (`^[a-z0-9][a-z0-9-]*$`). |
| `name` | Human-readable name. |
| `version` | The component's own version string. |
| `kind` | The manifest kind — fixed per schema (`client-profile`, `provider-profile`, `adapter`, `plugin`). |
| `capabilities` | The [capability labels](capabilities.md) this component publishes. |
| `compatibility` | The [compatibility block](versioning.md). Embeds `compatibility-v1.json` by `$ref`. |

The kind-specific block (`client`, `provider`, …) follows.

## Client profile

A client profile describes how requests from one client kind should be routed and
whether the companion attaches. The required `client.mode` field is one of `cli`,
`tui`, `api`, `sdk`, `ide`, `cron`, `batch`.

| `client` field | Meaning |
|---|---|
| `mode` | **Required.** How the client is consumed. |
| `companion_eligible` | Whether the client-side companion attaches. Typically `true` for `cli`/`tui`/`ide`; `false` for `api`/`sdk`, which run the full proxy pipeline instead. |
| `detection.header_signature` | Header pattern this client emits, used to detect it at runtime. |
| `detection.env_signature` | Environment-variable pattern the client sets. |

### Worked example — client profile

```json
{
  "tip_version": "TIP-1.0",
  "id": "claude-code",
  "name": "Claude Code",
  "version": "1.0.0",
  "kind": "client-profile",
  "capabilities": [
    "tip.companion.prompt-packaging",
    "tip.companion.session-journal"
  ],
  "compatibility": {
    "tip_version_range": ">=TIP-1.0,<TIP-2.0",
    "requires_profile": ["tip-proxy"]
  },
  "client": {
    "mode": "cli",
    "companion_eligible": true,
    "detection": {
      "header_signature": "X-Claude-Code-*",
      "env_signature": "CLAUDE_CODE_*"
    }
  }
}
```

## Provider profile

A provider profile describes how an outbound provider is invoked.
`provider.name` and `provider.endpoint_pattern` are required.

| `provider` field | Meaning |
|---|---|
| `name` | **Required.** Canonical provider name (`anthropic`, `openai`, `google`, `ollama`, …). |
| `endpoint_pattern` | **Required.** URL the provider accepts; `{name}` placeholders allowed for user-configured hostnames. |
| `auth_scheme` | `bearer`, `x-api-key`, `oauth`, or `none`. |
| `auth_header` | Header name carrying the credential (for `bearer` / `x-api-key`). |
| `models[]` | Known models with optional `input_price_per_million`, `output_price_per_million`, `context_window`, `supports_streaming`, `supports_tools`. Runtime discovery overrides this list; unknown models degrade gracefully. |
| `billing_routing_depends_on_body_bytes` | If `true`, this provider's billing routing depends on exact request bytes — the handling proxy must publish `tip.byte-preserved-passthrough`. |
| `trust.source_repo` / `trust.signed` | Provenance of the profile. |

### Worked example — provider profile

```json
{
  "tip_version": "TIP-1.0",
  "id": "anthropic",
  "name": "Anthropic",
  "version": "1.0.0",
  "kind": "provider-profile",
  "capabilities": [],
  "compatibility": {
    "tip_version_range": ">=TIP-1.0,<TIP-2.0"
  },
  "provider": {
    "name": "anthropic",
    "endpoint_pattern": "https://api.anthropic.com/v1/messages",
    "auth_scheme": "x-api-key",
    "auth_header": "x-api-key",
    "billing_routing_depends_on_body_bytes": true,
    "models": [
      {
        "id": "claude-opus-4-7",
        "context_window": 200000,
        "supports_streaming": true,
        "supports_tools": true
      }
    ]
  },
  "trust": {
    "source_repo": "https://github.com/tokenpak/registry",
    "signed": true
  }
}
```

Because `billing_routing_depends_on_body_bytes` is `true`, any proxy that routes
to this provider must publish `tip.byte-preserved-passthrough` — otherwise the
connection fails compatibility negotiation.

## Adapter & plugin manifests

Adapters and plugins share the same identity core and add their own block:

- **Adapter** (`kind: adapter`) — wires a client tool or framework to a proxy.
  Publishes `tip.adapter.client-integration` or `tip.adapter.framework-bridge`.
- **Plugin** (`kind: plugin`) — installs hooks at documented pipeline stages.
  Publishes `tip.plugin.hook-point`.

Both validate against their published schemas
([`adapter-v1.json`](https://docs.tokenpak.ai/schemas/manifests/adapter-v1.json),
[`plugin-v1.json`](https://docs.tokenpak.ai/schemas/manifests/plugin-v1.json)) and
must carry a `compatibility` block like every other manifest.

## See also

- [Capabilities](capabilities.md) — the labels a manifest lists.
- [Versioning & compatibility](versioning.md) — the embedded `compatibility` block.
- [Conformance](conformance.md) — validating a manifest against its schema.
