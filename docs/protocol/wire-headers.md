# Wire headers (`X-TokenPak-*`)

TIP-1.0 defines a family of `X-TokenPak-*` headers carried on data-plane requests
and responses. They are **informational metadata**: they describe what a TIP
component did with a request, but they never alter the request body. A component
on a passthrough path preserves the underlying provider request byte-for-byte and
attaches these headers alongside it.

- **Machine-readable source of truth:** [`headers-v1.json`](https://docs.tokenpak.ai/schemas/tip/headers-v1.json)

The schema sets `additionalProperties: true` — a component may carry its own
headers, but the names below are reserved by TIP-1.0 and carry the meanings
documented here.

## Core headers

| Header | Format | Direction | Meaning |
|---|---|---|---|
| `X-TokenPak-TIP-Version` | `TIP-<n>.<n>` | request + response | TIP version the emitter is using (e.g. `TIP-1.0`). **Required on every TIP-aware request and response.** |
| `X-TokenPak-Profile` | profile id | request + response | The emitter's profile: one of `tip-proxy`, `tip-companion`, `tip-adapter`, `tip-plugin`, `tip-dashboard-consumer`. |
| `X-TokenPak-Capability` | comma-separated labels | request | Capability labels the emitter publishes for this request. Each token is a `tip.<name>` or `ext.<ns>.<name>` label. |
| `X-TokenPak-Request-Id` | opaque string | request + response | Stable correlation id for telemetry, cache lookups, and logs. UUID v7 preferred. The request-side emitter sets it; the response-side echoes it unchanged. |

## Cache & savings headers

These appear on responses and follow the **honest-attribution** rule: cache and
compression savings are reported separately and never summed.

| Header | Format | Meaning |
|---|---|---|
| `X-TokenPak-Cache-Origin` | `proxy` \| `client` \| `unknown` | Who served an observed cache hit. `proxy` = the TokenPak cache; `client` = the provider's own cache (inferred from the response); `unknown` = cannot attribute. Present on every response telemetry row. |
| `X-TokenPak-Savings-Tokens` | integer string | Token savings attributed to **compression** for this request. Cache savings are reported separately; this header never folds the two together. Absent means zero or unmeasured. |
| `X-TokenPak-Savings-Cost` | decimal string (USD) | Cost savings attributed to this request, following the same compression-vs-cache attribution rule. |
| `X-TokenPak-Compression-Ms` | decimal string (ms) | Time spent in the compression stage. Part of the component's overhead budget. |

## Intent headers (opt-in)

A proxy can classify a request's intent. These headers are emitted **only** when
the resolved adapter publishes the `tip.intent.contract-headers-v1` capability;
otherwise they are kept in local telemetry and never put on the wire.

| Header | Format | Meaning |
|---|---|---|
| `X-TokenPak-Intent-Class` | lowercase token | The classified intent of the request (e.g. `code_change`, `debug`, `query`). |
| `X-TokenPak-Intent-Confidence` | decimal `0.0`–`1.0` | Classifier confidence in the intent. |
| `X-TokenPak-Intent-Subtype` | lowercase token | Optional refinement of the intent class (e.g. `bug_fix` under `code_change`). |
| `X-TokenPak-Contract-Risk` | `low` \| `medium` \| `high` | Risk classification of the resolved intent contract. |
| `X-TokenPak-Contract-Id` | opaque string | Identifier of the per-request intent contract. One-to-one with `X-TokenPak-Request-Id` in this release. |

!!! info "Why intent headers are gated"
    Intent headers only go on the wire when the receiving adapter has explicitly
    declared it understands them. This keeps the default request surface minimal
    and ensures a peer never receives headers it did not opt into — a direct
    application of the capability-negotiation rule in
    [Capabilities](capabilities.md).

## Worked example — request

A proxy forwarding a request it has compressed, with intent headers enabled
because the downstream adapter opted in:

```http
POST /v1/messages HTTP/1.1
Host: api.anthropic.com
X-TokenPak-TIP-Version: TIP-1.0
X-TokenPak-Profile: tip-proxy
X-TokenPak-Capability: tip.compression.v1,tip.byte-preserved-passthrough
X-TokenPak-Request-Id: 018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2
X-TokenPak-Intent-Class: code_change
X-TokenPak-Intent-Confidence: 0.82
X-TokenPak-Contract-Risk: medium
```

The request body below these headers is the unmodified provider payload.

## Worked example — response

The matching response, echoing the request id and reporting an attributed cache
hit plus compression savings:

```http
HTTP/1.1 200 OK
X-TokenPak-TIP-Version: TIP-1.0
X-TokenPak-Profile: tip-proxy
X-TokenPak-Request-Id: 018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2
X-TokenPak-Cache-Origin: proxy
X-TokenPak-Savings-Tokens: 1840
X-TokenPak-Savings-Cost: 0.0094
X-TokenPak-Compression-Ms: 7.3
```

Note that `X-TokenPak-Savings-Tokens` carries the **compression** figure only.
If a cache hit also saved tokens, that is recorded separately on the telemetry
row (see [Telemetry](telemetry.md)) and never added into the savings header.

## See also

- [Metadata](metadata.md) — the in-band metadata object that mirrors several of
  these header values.
- [Telemetry](telemetry.md) — how the response-side values land in the telemetry
  store.
- Registry schema: [`headers-v1.json`](https://docs.tokenpak.ai/schemas/tip/headers-v1.json)
