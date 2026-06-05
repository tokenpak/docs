# Recipe: Model Routing by Use Case

> **Status: Conceptual.** This recipe describes a use-case-based routing *pattern*. The declarative `routing:` / `routes:` / `keywords:` / `cost_aware_routing:` config block, the inline `model` / `provider` response fields, and the `tokenpak usage-report` command shown below are **illustrative** — they are not part of the validated config surface or shipped CLI of the current TokenPak release. The proxy is a byte-preserving passthrough and does not inject a chosen-model field into the response body. Confirm any CLI command against `tokenpak --help`.

**What this solves:** The pattern of sending each request to a model suited to the task — a stronger model for code, a smaller/cheaper one for simple chat.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- API keys for the providers you intend to use
- An understanding of which models suit which tasks

## The pattern (illustrative config)

The idea is to map request intent to a preferred model with a fallback. The YAML below is a **conceptual** illustration only — this routing schema is not the validated TokenPak config surface:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema
routing:
  enabled: true
  routes:
    - name: code_generation
      keywords: [code, function, debug, refactor, algorithm]
      preferred_model: gpt-4
      fallback_model: gpt-3.5-turbo
    - name: simple_chat
      keywords: [greet, hello, chat, casual]
      preferred_model: claude-haiku
      fallback_model: gpt-3.5-turbo
    - name: default
      preferred_model: gpt-3.5-turbo
      fallback_model: claude-haiku

cost_aware_routing:
  enabled: true
  degrade_above_budget_pct: 80
  degradation_map:
    gpt-4: gpt-3.5-turbo
```

## What's real today

- Start the proxy with `tokenpak serve` (default `http://127.0.0.1:8766`).
- The proxy forwards request and response bodies verbatim. The model that served a request is whatever your request specified and whatever the upstream returns — TokenPak does **not** add a `model_used` or `provider` field to the response body.
- Validate a proxy config file with `tokenpak config-check <file.json>`. The keyword-routing graph above is **not** part of that validated surface.
- To see recorded usage and cost, use `tokenpak status` (there is no `tokenpak usage-report` verb in the current release).

If you want per-request model selection today, choose the model in your application and send it in the request body:

```bash
tokenpak serve   # http://127.0.0.1:8766

curl -X POST http://127.0.0.1:8766/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-3-5-haiku-20241022", "max_tokens": 64,
       "messages": [{"role": "user", "content": "Hello, how are you?"}]}'
```

## Designing a routing strategy

If you implement routing in your application or an upstream layer, these principles apply:

- **Keep keywords specific** — overly broad terms match too much.
- **Always define a fallback** so an unavailable preferred model doesn't fail the request outright.
- **Degrade conservatively** — downgrade to a cheaper model only when the budget is genuinely tight, not early, to avoid hurting quality.
- **Resolve conflicts deterministically** — define a clear priority (e.g. longest/most-specific match wins) when multiple rules match.
- **Route on intent signals** (e.g. a system prompt), not on noisy user body text, to reduce false matches.

Routing a request to a smaller model where it suffices can reduce cost; the actual savings depend on your traffic mix and the models involved.
