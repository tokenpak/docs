# Versioning & compatibility

TIP versions are written `TIP-<MAJOR>.<MINOR>` — this release is **TIP-1.0**.
Every TIP-aware request and response carries the version it was emitted under in
the `X-TokenPak-TIP-Version` header (`TIP-1.0`), and every component declares the
version range it can speak in its manifest's `compatibility` block.

- **Machine-readable source of truth:** [`compatibility-v1.json`](https://docs.tokenpak.ai/schemas/tip/compatibility-v1.json)

## Version semantics

| Change | Bump | What a peer should expect |
|---|---|---|
| New optional field, new capability label, new error code | **MINOR** (`TIP-1.0` → `TIP-1.1`) | Additive only. Existing fields keep their meaning; older peers ignore what they do not recognize. |
| Removing or repurposing a field, tightening a required set, breaking a wire shape | **MAJOR** (`TIP-1.x` → `TIP-2.0`) | Not backward compatible. A peer that only speaks the older MAJOR may refuse to connect. |

The rule of thumb: **MINOR is safe to adopt without code changes; MAJOR is not.**
Declare the widest range you can actually honor so peers can negotiate against
the truth.

## The compatibility block

Every manifest embeds a `compatibility` object. Only `tip_version_range` is
required; the rest narrow the negotiation.

| Field | Meaning |
|---|---|
| `tip_version_range` | The version range this component speaks. **Required.** |
| `requires_peer_capabilities` | Capability labels the peer **must** publish. Missing any → the connection must fail. |
| `optional_peer_capabilities` | Capability labels the component uses if present, but does not require. |
| `requires_profile` | Profile identifier(s) the peer must advertise (e.g. an adapter that requires its peer be a `tip-proxy`). |
| `deprecated_since` | A `TIP-x.y` value marking this component as deprecated from that MINOR onward. Consumers should warn on use. |
| `removed_at` | A `TIP-x.y` value marking the end of the deprecation window. A component whose `removed_at` is at or before the current version must not connect. |

### Version range syntax

`tip_version_range` is a comma-separated list of predicates. Each predicate is an
operator followed by a `TIP-MAJOR.MINOR` value, and all predicates must hold:

```
<predicate>[,<predicate>...]   where <predicate> = (>= | > | <= | < | == | !=)TIP-<MAJOR>.<MINOR>
```

| Range | Means |
|---|---|
| `>=TIP-1.0,<TIP-2.0` | TIP-1.0 and any later 1.x, but not 2.x. The standard "I speak TIP-1" declaration. |
| `>=TIP-1.2` | TIP-1.2 and everything after, with no upper bound. |
| `==TIP-1.0` | Exactly TIP-1.0, nothing else. |

## Worked example

A provider adapter that speaks TIP-1.x, needs its peer to be a proxy that
preserves request bytes, and will opt into intent headers if the peer offers
them:

```json
{
  "tip_version_range": ">=TIP-1.0,<TIP-2.0",
  "requires_profile": ["tip-proxy"],
  "requires_peer_capabilities": [
    "tip.byte-preserved-passthrough"
  ],
  "optional_peer_capabilities": [
    "tip.intent.contract-headers-v1"
  ]
}
```

During connection negotiation the peer's published profile and capabilities are
checked against this block:

- If the peer is not a `tip-proxy`, or does not publish
  `tip.byte-preserved-passthrough`, the connection **must** fail with
  [`tip.capability.missing-required`](errors.md#error-code-catalog).
- If the peer also publishes `tip.intent.contract-headers-v1`, intent headers are
  exchanged; if not, they are simply omitted and the connection still succeeds.

## Deprecation lifecycle

A component is retired in two stages so downstream peers are never surprised:

```json
{
  "tip_version_range": ">=TIP-1.0",
  "deprecated_since": "TIP-1.3",
  "removed_at": "TIP-2.0"
}
```

1. From `TIP-1.3`, peers should emit a warning when they use this component but
   may still connect.
2. Once the current negotiated version reaches `removed_at` (`TIP-2.0`), the
   component must not connect.

## See also

- [Capabilities](capabilities.md) — the labels referenced by
  `requires_peer_capabilities`.
- [Profiles & manifests](profiles.md) — where the `compatibility` block lives.
- Registry schema: [`compatibility-v1.json`](https://docs.tokenpak.ai/schemas/tip/compatibility-v1.json)
