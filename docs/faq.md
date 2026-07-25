# TokenPak — Frequently Asked Questions

## General

### Is TokenPak production-ready?

TokenPak is currently in **OSS beta**. The proxy core, Prompt Packing pipeline, Spend Guard, Savings Ledger, and client integrations are stable and used in real workflows today. Some surfaces (Pak scoring/assembly, fleet orchestration, advanced recipes) are explicitly read-only or experimental in the beta — see [Known Issues](known-issues.md) for the current line.

We don't claim an SLA for the OSS package: TokenPak runs on your machine, so reliability is determined by your machine and the upstream provider, not by any infrastructure we operate.

### Is TokenPak free?

Yes. TokenPak is Apache 2.0 licensed and the package on PyPI (`pip install tokenpak`) is the full OSS product. No license activation, no feature gates inside the OSS package, no telemetry sent home by default.

### Why is it free?

TokenPak is built in the open because it works better that way. The protocol it implements (TIP-1.0) is a public spec; the proxy is its reference implementation. Sustainable open-source projects work when the source is honest, the docs match the code, and the development cadence is real — that's the bar we hold ourselves to.

### What providers does TokenPak support?

**Fully supported in the OSS beta:**

- Anthropic Claude (all models)
- OpenAI GPT-4, GPT-3.5
- Google Gemini
- Meta Llama (via Replicate or Hugging Face)
- Local Ollama

**Easy to add:** any REST-compatible LLM API. TokenPak's adapter pattern makes adding custom providers straightforward — see the [adapters guide](adapters.md).

---

## How It Works

### How does TokenPak route requests to providers?

You define a routing strategy in `config.yaml`:

```yaml
routing:
  primary: anthropic    # Default provider
  fallback: openai      # Backup if primary fails
  strategies:
    - provider: anthropic
      models: ["claude-3-*"]
    - provider: openai
      models: ["gpt-4", "gpt-3.5-turbo"]
```

TokenPak matches the requested model to a provider and routes there. If the provider fails, it automatically tries fallbacks. No code changes needed.

### Does TokenPak support streaming?

Yes, completely. TokenPak proxies Server-Sent Events (SSE) from providers without buffering. Your streaming requests work exactly as if you called the provider directly — you get chunks in real-time with full backpressure handling.

### How does caching work? Will I get stale responses?

TokenPak caches responses based on request hashing (model + prompt). Cache hits have a configurable TTL (default 1 hour), and you can disable caching per-request via headers. It's useful for repeated queries or batch processing, but not suited for live/dynamic content. For chat conversations, disable caching or use short TTLs.

### What about token counting? Is it accurate?

TokenPak uses native token counters for each provider (Anthropic's `token-counter`, OpenAI's `tiktoken`). We don't approximate — you get exact counts. For unsupported providers, we use a fallback estimator (~4 chars per token), which you can override.

---

## Security & Privacy

### Is my data stored? Is it encrypted?

Your data never leaves your machine. TokenPak runs locally and only talks to the upstream provider's API. No external logging, no analytics, no cloud component. Cached responses live in a local SQLite ledger (`~/.tokenpak/monitor.db` or `~/.tpk/monitor.db` on fresh installs) with a configurable TTL. Full details on the [tokenpak.ai privacy page](https://tokenpak.ai/compliance/privacy).

### How does rate limiting work?

TokenPak supports multiple rate-limiting strategies:

- **Per-provider:** respects each provider's rate limits (e.g., Claude's RPM limits).
- **Per-key:** limits by API key (useful for multi-tenant setups).
- **Per-user:** limits by user ID (requires middleware integration).

Limits are configurable in `config.yaml`. You get clear error messages when limits are exceeded.

### Can I audit requests for compliance?

Yes. Every request is logged to the local SQLite ledger with metadata (model, token counts, latency, cost, cache-origin). You can also wire up your own logging backend via webhooks.

---

## Performance & Operations

### What's the performance overhead?

**Proxy internals:** TokenPak adds modest compression overhead per request on typical agent prompts. Routing, token counting, and cache lookup are lightweight, in-memory operations.

**End-to-end latency:** when measured against direct API calls, the proxy adds some overhead due to the network round-trip and connection-pooling differences. This is expected for any local proxy.

**Context:** the latency overhead is acceptable because:

- Token savings dwarf the latency cost on real agent workloads.
- Cache hits eliminate provider round-trip latency entirely.
- Compression batching improves throughput for batch/async workloads.

For applications where sub-millisecond response time is critical, either run the proxy on the same machine as your client (recommended), or use the SDK in-process.

### Can I self-host TokenPak?

That's the only way to run TokenPak. You install the OSS package locally:

- **pip:** `pip install tokenpak && tokenpak start`
- **Docker:** `docker run -p 8766:8766 tokenpak/tokenpak`
- **Kubernetes:** Helm charts and manifests are in the repo

See the [installation guide](installation.md) for deployment options.

### How do I monitor TokenPak?

TokenPak exposes Prometheus metrics on `/metrics`:

- Request count, latency, error rates
- Token usage by model and provider
- Cache hit/miss rates
- Provider health status

You can scrape this in Prometheus, Datadog, or any metrics platform. Logs are JSON-formatted for easy parsing. The local dashboard (`tokenpak dashboard`) gives you a TUI + web view of the same data.

### What if a provider goes down? How does failover work?

TokenPak automatically detects provider failures via health checks and circuit breakers. When a provider is unhealthy, it routes to the fallback provider (no user action needed). Once the primary provider recovers, routing resumes. You can also manually force a provider state via the CLI (`tokenpak provider-status`).

---

## Customization & Integration

### How do I add a custom LLM provider?

TokenPak uses an adapter pattern. See the [adapters guide](adapters.md) for the full guide, but the quick version:

1. Create an adapter class inheriting from `BaseAdapter`.
2. Implement `send_request()` and `count_tokens()`.
3. Register it in `config.yaml`.

A full example with a local Ollama instance is in the docs.

### Can I use TokenPak with my favorite SDK (LangChain, LiteLLM, etc.)?

TokenPak speaks the OpenAI and Anthropic request shapes, so most SDKs work by changing the base URL to `http://localhost:8766`; your real API key stays where the SDK already reads it from. Tested adapters are OpenAI SDK, Anthropic SDK, and LiteLLM. Other OpenAI-compatible SDKs — LangChain, LlamaIndex, AutoGen, CrewAI — are expected to work but are not yet verified; see the adapter compatibility matrix for current status.

### Can I modify requests/responses in-flight?

Yes, via middleware. TokenPak supports request and response hooks:

```python
def log_request(request):
    print(f"Model: {request.model}, Tokens: {request.tokens}")
    return request

def log_response(response):
    print(f"Cost: ${response.cost}")
    return response
```

See the [plugin guide](plugin-guide.md) for the full hook surface.

---

## Cost & Budget

### How does TokenPak calculate costs?

TokenPak tracks input and output tokens and multiplies by provider pricing. Pricing is updated from provider public pricing pages. You can also configure custom rates in `config.yaml` (useful for negotiated enterprise pricing). Costs are logged per request and rolled up by session, agent, model, and provider.

### Can I set a budget/cost limit?

Yes — that's what **Spend Guard** does. It's shipped in the OSS beta as a pre-send circuit breaker:

```bash
tokenpak budget --help
```

Defaults are context-window-percentage based (90% warn / 100% hard stop). Dollar-based rolling caps are opt-in. When a request would exceed the cap, TokenPak returns HTTP 402 with `error.type=tokenpak_spend_guard_blocked` and a clear release directive — instead of letting a runaway agent burn through a budget. Full details in the Spend Guard section of the [configuration docs](configuration.md).

---

## Support & Community

### Where do I report bugs?

[GitHub Issues](https://github.com/tokenpak/tokenpak/issues). Include your OS, Python version, TokenPak version, and reproduction steps. We prioritize crashes and regressions.

### How do I request features?

[GitHub Discussions](https://github.com/tokenpak/tokenpak/discussions) for ideas, or [Issues](https://github.com/tokenpak/tokenpak/issues) if you have a detailed spec. We review requests weekly and prioritize based on community interest and alignment with the roadmap.

### How do I contribute?

We welcome bug fixes, docs, adapters, and tests. Fork, make your change, and open a PR. Good first issues are labeled [`good-first-issue`](https://github.com/tokenpak/tokenpak/labels/good-first-issue).

### Is there a Slack/Discord community?

We're using GitHub Discussions for now, which is lower-friction than chat. If the community asks for Slack, we'll set it up. Reach out in [Discussions](https://github.com/tokenpak/tokenpak/discussions) if you'd like to chat.
