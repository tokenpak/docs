# Recipe: Budget Caps & Spend Alerts

> **Status: Conceptual.** This recipe describes a spend-guard *pattern*. The declarative `budget:` config block, per-user limits, the inline `cost_cents` / `budget_exceeded` response fields, and the `sync-pricing` / `reconcile-spend` commands shown below are **illustrative** — they are not part of the validated config surface or shipped CLI of the current TokenPak release. The proxy is a byte-preserving passthrough and does not inject cost or error fields into the response body. Treat this as a design sketch, not a copy-paste runbook. Confirm any CLI command against `tokenpak --help`.

**What this solves:** The pattern of capping daily/monthly spend and reacting (alert, reject, or downgrade) as a budget is approached or exceeded.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- Valid API keys for your providers
- A monitoring sink (logs, webhook, or metrics store) if you want alerts

## The pattern (illustrative config)

The idea is to track estimated spend and take an action at thresholds. The YAML below is a **conceptual** illustration only — it is not the validated TokenPak proxy config schema:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema
budget:
  enabled: true
  daily_limit_cents: 1000     # $10.00/day
  monthly_limit_cents: 20000  # $200.00/month
  alert_threshold_pct: 80
  alert_webhook: https://monitoring.example.com/budget-alert
  reject_on_exceed: true
  # Optional graceful degradation: route to a cheaper model instead
  fallback_model_on_exceed: gpt-3.5-turbo
```

## What's real today

- Start the proxy with `tokenpak serve` (default `http://127.0.0.1:8766`).
- TokenPak records usage out-of-band; inspect it with `tokenpak status`. Cost is **not** returned inline in the response body — the proxy forwards the upstream response verbatim.
- Validate a proxy config file with `tokenpak config-check <file.json>`. The declarative `budget:` graph above is **not** part of that validated surface.

A request against the proxy returns the upstream provider's response unchanged:

```bash
tokenpak serve   # http://127.0.0.1:8766

curl -X POST http://127.0.0.1:8766/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 64,
       "messages": [{"role": "user", "content": "Write 100 words"}]}'
```

To see spend after running requests, use `tokenpak status` (recorded server-side), rather than reading a `cost_cents` field from the response.

## Designing a budget guard

If you implement spend control (in your application or your own orchestration), these principles apply:

- **Keep cost estimates current.** Provider pricing changes; a stale hardcoded rate drifts from reality. Refresh pricing from an authoritative source rather than hardcoding it indefinitely.
- **Make alerting reliable.** A single webhook with no retry can fail silently — use retries or a secondary channel.
- **Distribute per-user limits** so a single user can't consume the whole budget.
- **Leave headroom for in-flight requests** — block somewhat below the hard cap so a request already underway can complete.
- **Reconcile estimates against real invoices** periodically — estimate-based tracking drifts from actual billing over time.
