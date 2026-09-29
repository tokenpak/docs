# TokenPak vs. Alternatives: Feature Comparison

This comparison covers the most popular LLM proxy and observability solutions. We've researched each alternative's current capabilities directly from their documentation and GitHub repositories. Our goal is to help you understand when TokenPak is the right choice—and when alternatives might better suit your needs.

---

## Feature Comparison Matrix

| Feature | TokenPak | LiteLLM | Helicone | OpenRouter |
|---------|----------|---------|----------|-----------|
| **Self-hosted** | ✅ Yes | ✅ Yes | ⚠️ Cloud or self-hosted (Docker) | ❌ Cloud only |
| **Open source** | ✅ Yes (Apache 2.0) | ✅ Yes (MIT) | ✅ Yes (Apache 2.0) | ❌ Proprietary |
| **Provider support** | 4 (Claude, Gemini, OpenAI, Ollama) | 100+ | 20+ | 150+ |
| **Vault compression** | ⚠️ Explicit tools only (not applied to default requests) | ❌ No | ❌ No | ❌ No |
| **Token counting accuracy** | ⚠️ Provider-reported usage where available; estimates are labelled | ✅ Native (per-provider) | ✅ Native | ⚠️ Approximate |
| **Cost tracking per-request** | ✅ Yes | ✅ Yes (with dashboard) | ✅ Yes (with dashboard) | ✅ Yes (cloud only) |
| **Streaming support** | ✅ Full SSE | ✅ Full SSE | ✅ Full SSE | ✅ Full SSE |
| **Python SDK** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **JavaScript/TypeScript SDK** | ⚠️ HTTP client only | ✅ Yes | ✅ Yes | ✅ Yes |
| **Docker support** | ✅ Yes | ✅ Yes | ✅ Yes (production-grade Helm) | ❌ Cloud only |
| **Proxy overhead** | Designed for minimal local overhead | Local proxy (self-hosted) | Depends on self-host | Network-bound (cloud-routed) |
| **Caching** | ✅ LRU (TTL-based) | ⚠️ Via enterprise integrations | ✅ Via observability | ❌ No |
| **Automatic failover** | ⚠️ Not active by default (observe-mode routing records) | ✅ Yes (routing) | ⚠️ Via AI Gateway (newer) | ❌ No |
| **No cloud logging by the proxy** | ✅ Yes (records stay on your machine) | ✅ Yes (with config) | ⚠️ Logs to platform (GDPR compliant) | ❌ Logs to cloud |
| **Rate limiting** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes (cloud-side) |
| **Free tier** | ✅ Yes (unlimited, self-hosted) | ✅ Yes (limited requests) | ✅ Yes (10k/month) | ✅ Yes ($5 initial credit) |

---

## Detailed Comparison

### TokenPak
**Position:** A local proxy for coding agents that records each request and shows how far the session can go: measured usage, estimated cost, burn and runway.

**Strengths:**
- **Short setup** — `pip install tokenpak && tokenpak serve` — running in minutes
- **Session trip computer** — Measured usage, estimated cost, burn and runway, on by default in the Claude Code footer and the Codex pane and in `tokenpak status`; forecasts appear only where calibrated
- **Explicit context tools** — Compression operations and vault indexing that you invoke can reduce eligible content; the default proxy preserves conversation turns, so a forwarded request can report zero tokens saved
- **No added cloud service** — Requests go to the provider you already use, credentials stay in your existing client and provider flow, and TokenPak does not persist them
- **Lightweight proxy** — Designed to add minimal overhead in front of your providers
- **Apache 2.0 licensed core** — Permissive open source; TokenPak Pro is proprietary
- **Cost tracking** — Per-request cost recorded locally from provider-reported usage where available, with estimates labelled

**Trade-offs:**
- Fewer provider integrations (4 core: Claude, Gemini, OpenAI, Ollama) vs. 100+ in LiteLLM
- A local dashboard and `tokenpak status`, not a hosted observability platform
- Automatic failover and model changes are not active by default
- Smaller ecosystem and community

**Best for:**
- Developers and tech leads running long coding-agent sessions in Claude Code or Codex who want to see what a session has used, what finishing will likely cost, and how far it can go
- Projects with **Anthropic + OpenAI + Gemini** as primary providers
- Developers who want to **run locally** with no TokenPak cloud service
- Applications where **keeping proxy overhead low** is a priority

**When NOT to use TokenPak:**
- If you need support for 50+ niche LLM providers (LiteLLM is better)
- If you need a comprehensive observability dashboard (Helicone is better)
- If you want no infrastructure overhead (OpenRouter cloud-only is simpler)
- If you need a hosted, multi-tenant or centrally managed proxy

---

### LiteLLM
**Position:** Universal LLM proxy for multi-provider routing at scale.

**Strengths:**
- **Provider breadth** — Supports 100+ LLMs (every major provider + emerging models)
- **Production-grade routing** — Advanced retry, fallback, and load-balancing logic
- **Admin dashboard** — Web UI for monitoring, cost tracking, virtual keys
- **Extensive enterprise features** — Authentication, user management, rate limiting per project
- **Framework integrations** — Works with LangChain, LlamaIndex, Semantic Kernel, etc.
- **Well-established** — 8+ years of battle-tested routing logic

**Trade-offs:**
- **Heavier footprint** — More moving parts can add overhead compared to a minimal proxy
- **More complex setup** — Requires database (Postgres), Redis, Prometheus for full features
- **No vault compression** — Focuses on provider routing, not prompt optimization
- **Data logging optional** — Default behavior sends telemetry; requires config to disable

**Best for:**
- Teams routing across **many providers** (OpenAI, Azure, Bedrock, Cohere, etc.)
- **Multi-tenant platforms** (need user/project isolation and billing)
- Organizations needing **admin dashboards** and user management
- Projects using **LangChain** or other popular frameworks
- **Enterprise deployments** with strict SLAs

**When NOT to use LiteLLM:**
- If you want to **avoid logging infrastructure** (TokenPak adds no cloud service)
- If you want the **leanest possible proxy footprint** (TokenPak is intentionally minimal)
- If you want TokenPak's **explicit context tools**, such as vault compression
- If you're a solo developer (overkill for small projects)

---

### Helicone
**Position:** All-in-one LLM observability platform (cloud or self-hosted).

**Strengths:**
- **Observability-first design** — Session tracing, debugging, prompt management built-in
- **AI Gateway** — Access 100+ models through Helicone with automatic fallbacks
- **Free tier** — 10k requests/month free (generous for testing)
- **Production-grade self-hosting** — Docker Compose + Helm for on-prem deployments
- **Fine-tuning partnerships** — Native integration with OpenPipe and Autonomi
- **Enterprise compliance** — SOC 2 and GDPR certified
- **Dataset management** — Export logs for fine-tuning directly from the platform

**Trade-offs:**
- **Data sharing by design** — Logs flow to Helicone's platform (even self-hosted, you own data)
- **Larger footprint** — 5+ services (Next.js, Cloudflare Workers, Express, Supabase, ClickHouse, Minio)
- **Requires external dependencies** — Supabase for auth, ClickHouse for analytics
- **Learning curve** — More features = more complexity for simple use cases

**Best for:**
- Teams wanting **observability dashboards** (sessions, traces, request debugging)
- Projects needing **prompt management and versioning**
- Organizations **fine-tuning custom models** (direct OpenPipe integration)
- Teams wanting **cloud simplicity** without managing infrastructure
- **Regulated industries** needing SOC 2 compliance

**When NOT to use Helicone:**
- If you want **no hosted logging platform** in the request path (TokenPak adds no cloud service)
- If you want **minimal setup overhead** (TokenPak or cloud-only solutions better)
- If you want the **leanest proxy footprint** (a full observability stack adds more moving parts)
- If you only use 2-3 providers (TokenPak or LiteLLM simpler)

---

### OpenRouter
**Position:** Cloud-only LLM marketplace with 150+ models.

**Strengths:**
- **Model breadth** — 150+ models (newest releases appear faster than elsewhere)
- **Simplicity** — No infrastructure; just an API key and `base_url`
- **Competitive pricing** — Model arbitrage (cheaper than direct APIs for many models)
- **Easy integration** — Drop-in replacement for OpenAI SDK
- **No setup** — Works immediately; no proxy to run locally

**Trade-offs:**
- **Cloud-only** — No self-hosting; all requests route through OpenRouter's servers
- **Proprietary** — Closed source; can't modify or audit the code
- **Data sharing required** — Requests logged to OpenRouter (privacy concern for sensitive data)
- **No caching** — Redundant requests always hit the model
- **Cost opacity** — Pricing varies by model; harder to predict costs
- **Token counting approximate** — Uses estimates, not native counting
- **No failover** — If OpenRouter is down, you're blocked

**Best for:**
- **Rapid prototyping** — Try many models quickly without setup
- **Cost arbitrage projects** — Accessing cheaper model pricing
- **Teams comfortable with cloud solutions** (no on-prem requirement)
- **Side projects or MVPs** (no infrastructure overhead)

**When NOT to use OpenRouter:**
- If you do not want a **hosted service in the request path** (TokenPak adds no cloud service; requests go to the provider you already use)
- If you want **per-request cost records on your own machine** (TokenPak records them locally)
- If you want a **local proxy** rather than a hosted marketplace (TokenPak)
- If you need **redundancy and failover** (LiteLLM)

---

## Quick Decision Tree

```
Do you run long coding-agent sessions in Claude Code or Codex and want to see usage, cost and runway?
├─ YES → TokenPak (local proxy, no cloud service added)
└─ NO → Continue...

Do you route to 20+ different LLM providers?
├─ YES → LiteLLM (100+ provider support)
└─ NO → Continue...

Do you need observability dashboards and prompt versioning?
├─ YES → Helicone (cloud or self-hosted)
└─ NO → Continue...

Do you want the simplest setup (no local infrastructure)?
├─ YES → OpenRouter (cloud-only, instant)
└─ NO → TokenPak (lightweight, self-hosted)
```

---

## When to Choose Alternatives Instead of TokenPak

### Choose **LiteLLM** if:
- You need to route to 50+ providers (not just Claude, Gemini, OpenAI)
- You're building a **multi-tenant platform** (user isolation, billing per user)
- You want an **admin dashboard** for non-technical users
- Your team is already using **LangChain** or similar frameworks

### Choose **Helicone** if:
- You need **session tracing and debugging** (watch agent conversations in real time)
- You're **fine-tuning models** (OpenPipe integration is native)
- You want **observability first** (cost analytics, request debugging, prompt management)
- You need **SOC 2 compliance** (your customers demand it)

### Choose **OpenRouter** if:
- You want **zero infrastructure** (cloud-only)
- You're **trying new models quickly** (150+ available immediately)
- You're **cost-arbitraging** (some models cheaper via OpenRouter)
- You don't need **local request handling or data sovereignty** (cloud routing and logging are acceptable)

---

## What TokenPak Focuses On

1. **Session Trip Computer** — Measured usage, estimated cost, burn and runway for a coding-agent session, on by default in the Claude Code footer and the Codex pane and in `tokenpak status`. Forecasts appear only where calibrated.

2. **Measured Receipts** — Each request is recorded locally, and the first request gives you a measured receipt. A forwarded request can truthfully report zero tokens saved.

3. **No Added Cloud Service** — Requests go to the provider you already use, credentials stay in your existing client and provider flow, and TokenPak does not persist them.

4. **Short Setup** — `pip install tokenpak && tokenpak serve` — no external database, no Redis, no other infrastructure.

5. **Lightweight by Design** — A minimal proxy layer intended to add little overhead in front of your providers. Receipt-backed performance figures will publish once TokenPak's benchmark suite produces a validated run.

---

## Cost Comparison

| Scenario | TokenPak | LiteLLM | Helicone | OpenRouter |
|----------|----------|---------|----------|-----------|
| **Infrastructure** | Free (self-hosted) | Free (self-hosted) | $0/mo (10k free tier) or $50+/mo (cloud) | $0 (no infra) |
| **API costs (100k requests/mo)** | Pass-through | Pass-through | Pass-through | Pass-through |
| **Repeated-context caching** | ⚠️ Provider cache reuse is separate from TokenPak context reduction; explicit context tools can reduce eligible content | ❌ No built-in caching | ❌ Observability-focused (no caching) | ❌ No caching |
| **Cost profile** | Pass-through, with measured usage and estimated cost recorded locally | Pass-through only | Pass-through + platform | Pass-through (cloud) |

Actual cost impact depends on your traffic and how much repeated context your workload contains. The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved. Receipt-backed savings figures will publish once TokenPak's benchmark suite produces a validated run.

---

## Integration Examples

### TokenPak
```python
# Point your existing provider SDK at the local TokenPak proxy
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### LiteLLM
```python
from litellm import completion

response = completion(
    model="anthropic/claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Hello!"}],
    base_url="http://localhost:4000"  # your proxy
)
```

### Helicone
```python
import openai

client = openai.OpenAI(
    base_url="https://ai-gateway.helicone.ai",
    api_key="<your-helicone-key>"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### OpenRouter
```python
import openai

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<your-openrouter-key>"
)

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Sources & Verification

- **LiteLLM:** https://github.com/BerriAI/litellm (Latest commit: 2026-03-25)
- **Helicone:** https://github.com/Helicone/helicone (Latest commit: 2026-03-25)
- **OpenRouter:** https://openrouter.ai (Public docs: 2026-03-25)
- **TokenPak:** https://github.com/tokenpak/tokenpak (Receipt-backed performance figures will publish once TokenPak's benchmark suite produces a validated run.)

---

## Summary

**TokenPak** is built for developers and tech leads running long coding-agent sessions who want to see usage, cost and runway. It adds no cloud service and keeps request records on your machine.

**Choose alternatives** if you need **multi-provider routing at scale** (LiteLLM), **observability dashboards** (Helicone), or **zero infrastructure** (OpenRouter).

The best choice depends on your priorities: session visibility vs. provider breadth, self-hosted vs. cloud, simplicity vs. features.

---

**Questions?** Open an issue on [TokenPak's GitHub](https://github.com/tokenpak/tokenpak) or check the [FAQ](faq.md).
