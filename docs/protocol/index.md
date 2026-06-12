# TIP-1.0 — TokenPak Integration Protocol

**TIP-1.0** is the contract a component implements to interoperate with TokenPak.
If you are building an adapter, a plugin, an alternate proxy, a dashboard, or any
tool that sits on the same wire as TokenPak, this section is the normative
reference for the headers, metadata, manifests, capabilities, telemetry, and
error shapes you are expected to produce and consume.

> **You do not need this section to *use* TokenPak.** `pip install tokenpak` and
> you are done. TIP-1.0 is for **implementers** — third-party integration
> authors and CI tooling — not end users.

## What TIP-1.0 covers

TIP-1.0 is a small, stable surface. It standardizes:

- **Wire headers** — the `X-TokenPak-*` headers carried on data-plane requests
  and responses. See [Wire headers](wire-headers.md).
- **Request/response metadata** — the runtime metadata object attached to a
  request and its response. See [Metadata](metadata.md).
- **Capabilities** — the labels a component publishes to declare what it does.
  See [Capabilities](capabilities.md).
- **Profiles & manifests** — the manifest shapes for the five component
  profiles. See [Profiles & manifests](profiles.md).
- **Telemetry** — the canonical per-request telemetry row. See
  [Telemetry](telemetry.md).
- **Errors** — the one error envelope every TIP surface emits. See
  [Errors](errors.md).
- **Versioning & compatibility** — how components declare the TIP versions and
  peer capabilities they require. See [Versioning & compatibility](versioning.md).

It deliberately does **not** cover the request body itself. TIP headers are
informational metadata; they never alter the bytes of the underlying provider
request. A TIP-aware component on a passthrough path preserves the request body
byte-for-byte.

## The canonical schemas

Every shape in TIP-1.0 has a machine-readable JSON Schema published on the
registry. These `$id` URLs are the authoritative source of truth — this prose
describes them, but the schema files define them.

| Area | Schema |
|---|---|
| Wire headers | [`headers-v1.json`](https://docs.tokenpak.ai/schemas/tip/headers-v1.json) |
| Metadata | [`metadata-v1.json`](https://docs.tokenpak.ai/schemas/tip/metadata-v1.json) |
| Capabilities | [`capabilities-v1.json`](https://docs.tokenpak.ai/schemas/tip/capabilities-v1.json) |
| Telemetry event | [`telemetry-event-v1.json`](https://docs.tokenpak.ai/schemas/tip/telemetry-event-v1.json) |
| Error envelope | [`error-v1.json`](https://docs.tokenpak.ai/schemas/tip/error-v1.json) |
| Compatibility | [`compatibility-v1.json`](https://docs.tokenpak.ai/schemas/tip/compatibility-v1.json) |

Four **manifest** schemas describe the components that speak TIP:

| Manifest | Schema |
|---|---|
| Adapter | [`adapter-v1.json`](https://docs.tokenpak.ai/schemas/manifests/adapter-v1.json) |
| Plugin | [`plugin-v1.json`](https://docs.tokenpak.ai/schemas/manifests/plugin-v1.json) |
| Client profile | [`client-profile-v1.json`](https://docs.tokenpak.ai/schemas/manifests/client-profile-v1.json) |
| Provider profile | [`provider-profile-v1.json`](https://docs.tokenpak.ai/schemas/manifests/provider-profile-v1.json) |

!!! note "Schema filename vs. published `$id`"
    On the registry the schema *files* are named `<name>.schema.json` (for
    example `headers.schema.json`). The **canonical identifier** is the
    published `$id` URL — the hyphenated `-v1.json` form shown in the tables
    above (`https://docs.tokenpak.ai/schemas/tip/headers-v1.json`). Always
    reference the published `$id` URL, not the source filename, when you cite a
    TIP schema or write a `$ref`.

## Component profiles

A TIP component advertises exactly one **profile** describing its role. The
profile identifier appears in the `X-TokenPak-Profile` header and in the
component's manifest.

| Profile | Role |
|---|---|
| `tip-proxy` | Sits on the data plane, applies compression / routing / caching, and emits telemetry. |
| `tip-companion` | Client-side, pre-send optimizer (CLI/TUI helpers, memory capsules, session journal). |
| `tip-adapter` | Wires a specific client tool or framework to a TIP-proxy. |
| `tip-plugin` | Registers hooks at documented pipeline stages. |
| `tip-dashboard-consumer` | Reads the telemetry store and presents derived, read-only views. |

Each profile has a small set of capabilities it is expected to publish. See
[Capabilities](capabilities.md) for the catalog and
[Profiles & manifests](profiles.md) for the manifest shapes.

## Design rules every TIP component follows

These three rules run through every schema in this section:

1. **Byte fidelity on passthrough.** Informational headers and metadata never
   change the underlying request body. Where billing or routing depends on exact
   bytes (for example provider cache controls), the proxy preserves the body
   without re-serializing it.
2. **Honest attribution.** A component never over-claims. Cache savings and
   compression savings are reported as **separate** numbers and never summed
   into one figure. When a cache hit cannot be attributed, it is classified
   `unknown` rather than guessed.
3. **Errors teach.** Every error uses the [error envelope](errors.md), names its
   cause, and points at the next step. Bare, unstructured error bodies are not
   conformant.

## Reading order

If you are implementing TIP-1.0 for the first time, read in this order:

1. [Versioning & compatibility](versioning.md) — how you declare what you speak.
2. [Capabilities](capabilities.md) — how you declare what you do.
3. [Profiles & manifests](profiles.md) — the manifest you publish.
4. [Wire headers](wire-headers.md) and [Metadata](metadata.md) — what you put on
   the wire.
5. [Telemetry](telemetry.md) and [Errors](errors.md) — what you record and what
   you return when things go wrong.
6. [Conformance](conformance.md) — how to verify your implementation.
