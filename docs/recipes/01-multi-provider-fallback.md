# Recipe: Multi-Provider Fallback

> **Status: Conceptual.** This recipe describes a failover *pattern*. The declarative `fallback_to` config keys and the failover log output shown below are **illustrative** — they are not a validated config surface of the current TokenPak release, and the proxy does not emit those messages inline. Treat this as a design sketch, not a copy-paste runbook. Confirm any CLI command against `tokenpak --help` before relying on it.

**What this solves:** The pattern of routing requests to a backup provider when your primary provider experiences an outage or rate limit.

## Prerequisites
- TokenPak installed: `pip install tokenpak`
- Valid API keys for the providers you intend to use
- `tokenpak` CLI available in your shell (`tokenpak --help`)

## The pattern (illustrative config)

The idea is to declare a primary model and a fallback target so that a failed request retries against a different provider. The YAML below is a **conceptual** illustration of how such a config might read — it is not the validated schema of the shipped proxy:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema
providers:
  openai:
    type: openai
    api_key: ${OPENAI_API_KEY}
  anthropic:
    type: anthropic
    api_key: ${ANTHROPIC_API_KEY}

models:
  gpt-4:
    provider: openai
    # Conceptual: try OpenAI first, then Anthropic
    fallback_to: claude-3-sonnet
  claude-3-sonnet:
    provider: anthropic
```

## What's real today

- Start the proxy with `tokenpak serve` (default `http://127.0.0.1:8766`).
- Validate a proxy config file with `tokenpak config-check <file.json>`. The shipped proxy config surface is a JSON file; for the server block, `config-check` recommends `server: { port: 8766, host: '127.0.0.1' }`. The elaborate `fallback_to` model graph above is **not** part of that validated surface.
- TokenPak's proxy is a **byte-preserving passthrough** — it forwards request and response bodies verbatim. It does **not** inject failover status messages or extra fields into the response body.

A request against the proxy looks like:

```bash
tokenpak serve   # listens on http://127.0.0.1:8766

# In another terminal:
curl -X POST http://127.0.0.1:8766/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 64,
    "messages": [{"role": "user", "content": "Say OK"}]
  }'
```

The response body is whatever the upstream provider returns, passed through unchanged.

## Designing a fallback strategy

If you implement failover (in your application or via your own orchestration in front of the proxy), the principles below apply regardless of how the routing is configured:

- **Chain across different providers**, not just different models of the same provider — an outage often takes out a whole provider.
- **Avoid fallback loops** — never let a chain point back to a model already tried.
- **Pre-check every key in the chain** so the fallback isn't itself unauthenticated.
- **Check the fallback's rate limits** — a fallback with a much lower limit can become the new bottleneck during an incident.
