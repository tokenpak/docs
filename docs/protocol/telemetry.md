# Telemetry

A TIP-proxy records **one telemetry row per request** in the telemetry store
(`~/.tokenpak/telemetry.db`). The row is the canonical, machine-readable record
of what happened to a request — provider, timing, token counts, savings, and
cache attribution — and it is what a `tip-dashboard-consumer` reads.

- **Machine-readable source of truth:** [`telemetry-event-v1.json`](https://docs.tokenpak.ai/schemas/tip/telemetry-event-v1.json)

The schema is **closed** (`additionalProperties: false`); extension data goes
under `ext`. Four fields are **required**: `request_id`, `timestamp`,
`cache_origin`, and `tip_version`.

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `request_id` | string | Matches the `X-TokenPak-Request-Id` header. |
| `timestamp` | RFC 3339 date-time | When the request arrived at the proxy. |
| `cache_origin` | `proxy` \| `client` \| `unknown` | Cache-hit attribution for this request. Never over-claimed. |
| `tip_version` | `TIP-<n>.<n>` | TIP version the event was emitted under. |

## Identity & status

| Field | Type | Meaning |
|---|---|---|
| `profile` | string | Emitter profile. |
| `provider` | string \| null | Outbound provider, or `null` if the request never reached one (cache hit, policy reject). |
| `model` | string \| null | Model id; `null` when `provider` is `null`. |
| `client` | string \| null | Client tool identifier. |
| `status` | integer | HTTP-style status of the response (`200`, `401`, `429`, `500`, …). `0` if rejected before any response shape existed. |
| `error_code` | string \| null | TIP [error code](errors.md) when the request failed; `null` on success. |

## Savings — compression and cache kept separate

The honest-attribution rule is enforced by the schema: compression savings and
cache savings live in **different fields** and are never summed.

| Field | Type | Meaning |
|---|---|---|
| `savings_tokens` | integer ≥ 0 | Compression token savings. |
| `savings_cost` | number ≥ 0 | Compression cost savings (USD). |
| `savings_cache_tokens` | integer ≥ 0 | Cache-attributable token savings, classified by `cache_origin`. |
| `savings_cache_cost` | number ≥ 0 | Cache-attributable cost savings (USD). |

## Timing

| Field | Type | Meaning |
|---|---|---|
| `compression_ms` | number ≥ 0 | Time in the compression stage. |
| `proxy_ms` | number ≥ 0 | Time in the proxy pipeline excluding the provider round-trip. |
| `provider_ms` | number ≥ 0 | Provider round-trip time, from outbound dispatch to first response byte. |

## Token counts & reasoning usage

| Field | Type | Meaning |
|---|---|---|
| `tokens_in` | integer ≥ 0 | Input tokens billed by the provider. |
| `tokens_out` | integer ≥ 0 | Output tokens billed by the provider. For reasoning models this may roll up visible and reasoning tokens. |
| `reasoning_tokens` | integer \| null | Reasoning/deliberation tokens consumed but not surfaced as visible content. Populated when the provider exposes reasoning usage (e.g. extended thinking / reasoning-effort models); `null` otherwise. |
| `visible_output_tokens` | integer \| null | Output tokens that became user-visible content; excludes `reasoning_tokens`. `null` when the provider does not split them. |
| `total_billable_tokens` | integer \| null | Authoritative total for cost; preferred over local estimates. `null` when the provider usage object was unavailable. |
| `reasoning_effort` | `low` \| `medium` \| `high` \| null | Provider-reported reasoning-effort tier, when applicable. |
| `reasoning_usage_source` | `provider_usage_object` \| `estimated` \| `unavailable` \| null | Provenance of the reasoning-usage fields. `estimated` is only acceptable for non-billing-critical telemetry. |
| `capabilities_negotiated` | string[] | Capability labels active for this request. |
| `ext` | object | Namespaced extension fields. |

## Worked example — a telemetry row

A successful request to Anthropic that the proxy compressed and served partly
from a provider-side cache hit:

```json
{
  "request_id": "018f3b2c-7a41-7c9e-9b00-2d6f5a1e44c2",
  "timestamp": "2026-06-12T15:32:08Z",
  "tip_version": "TIP-1.0",
  "profile": "tip-proxy",
  "provider": "anthropic",
  "model": "claude-opus-4-7",
  "client": "claude-code",
  "cache_origin": "client",
  "status": 200,
  "error_code": null,
  "savings_tokens": 1840,
  "savings_cost": 0.0094,
  "savings_cache_tokens": 12030,
  "savings_cache_cost": 0.0361,
  "compression_ms": 7.3,
  "proxy_ms": 11.2,
  "provider_ms": 1840.5,
  "tokens_in": 5120,
  "tokens_out": 612,
  "reasoning_tokens": 0,
  "visible_output_tokens": 612,
  "total_billable_tokens": 5732,
  "reasoning_usage_source": "provider_usage_object",
  "capabilities_negotiated": ["tip.compression.v1", "tip.cache.provider-observer"]
}
```

Read the savings honestly: the proxy's **compression** saved 1,840 tokens
(`savings_tokens`); a **provider-side cache hit** (`cache_origin: client`) saved a
further 12,030 (`savings_cache_tokens`). They are two separate numbers — a
conformant dashboard reports them separately and never adds them into a single
"savings" figure.

## See also

- [Wire headers](wire-headers.md) — the response headers these fields mirror.
- [Errors](errors.md) — the `error_code` values used here.
- Registry schema: [`telemetry-event-v1.json`](https://docs.tokenpak.ai/schemas/tip/telemetry-event-v1.json)
