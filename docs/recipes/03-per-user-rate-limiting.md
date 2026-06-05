# Recipe: Per-User Rate Limiting

> **Status: Conceptual.** This recipe describes a per-user rate-limiting *pattern*. The elaborate `user_tiers` / `user_assignments` config block (per-tier `rps`, `burst`, `enforce: queue|degrade`, etc.) and the inline `status` / `cost_cents` response fields shown below are **illustrative** — they are not part of the validated config surface of the current TokenPak release, and the proxy does not inject those fields into the response body. A flat, global rate-limit setting *does* exist (see "What's real today"). Confirm any CLI command against `tokenpak --help`.

**What this solves:** The pattern of giving different users different request-rate budgets so heavy users don't throttle casual ones.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- A way to identify users (API key or token) in your requests
- A sense of your expected per-user request rates

## The pattern (illustrative config)

The idea is to assign each user a tier with its own rate budget. The YAML below is a **conceptual** illustration only — the tiered schema is not the validated TokenPak config surface:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema
rate_limit:
  enabled: true
  default_rps: 10
  user_tiers:
    free:       { rps: 5,   burst: 2,   window_seconds: 60 }
    standard:   { rps: 50,  burst: 10,  window_seconds: 60 }
    enterprise: { rps: 500, burst: 100, window_seconds: 60 }
  user_assignments:
    user-123: { tier: free }
    user-456: { tier: standard }
  enforce: reject   # conceptual options: reject (429) | queue | degrade
```

## What's real today

- Start the proxy with `tokenpak serve` (default `http://127.0.0.1:8766`).
- The shipped proxy config (validated by `tokenpak config-check <file.json>`) supports **flat, global** rate-limit fields — `rate_limit_requests` and `rate_limit_window` — not the per-user tier graph above. There is no validated per-user-tier surface in the current release.
- The proxy is a byte-preserving passthrough: a rejected or accepted request is reflected by the **HTTP status code and body of the actual response**, not by a `status` or `cost_cents` field injected into the JSON body.

```bash
tokenpak serve   # http://127.0.0.1:8766

# A normal request; check the HTTP status with -i / -w, not a body field:
curl -i -X POST http://127.0.0.1:8766/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 16,
       "messages": [{"role": "user", "content": "Hi"}]}'
```

## Designing per-user rate limits

If you need true per-user tiers, implement them in your application or an upstream gateway. These principles apply regardless:

- **Differentiate tiers clearly** instead of one uniform limit for everyone.
- **Allow a small burst** to absorb legitimate traffic spikes without rejecting on the very next request.
- **Keep tier assignment fresh** — a user who upgrades should not stay on the old tier.
- **Prefer predictable windows** (fixed windows are easier to reason about than fine-grained sliding ones).
- **Keep burst small relative to the rate** so it smooths spikes rather than enabling abuse.
