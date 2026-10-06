# TokenPak — Frequently Asked Questions

## General

### Is TokenPak production-ready?

TokenPak is alpha-stage open-source software. The proxy core, Spend Guard, request records and the Claude Code and Codex integrations ship in the current release; interfaces can still change. The default proxy forwards the request and preserves conversation turns; explicit context and compression tools are separate. Some surfaces (Pak scoring and assembly, fleet orchestration, advanced recipes) are read-only or experimental — see [Known Limitations](KNOWN_LIMITATIONS.md) for the current line.

We don't claim an SLA for the OSS package: TokenPak runs on your machine, so reliability is determined by your machine and the upstream provider, not by any infrastructure we operate.

### Is TokenPak free?

Yes. The TokenPak core is Apache 2.0 licensed, and `pip install tokenpak` installs it. It needs no license key and sends no telemetry by default. Pro is a separate, proprietary package.

### Why is it free?

TokenPak is built in the open because it works better that way. The protocol it implements (TIP-1.0) is a public spec; the proxy is its reference implementation. Sustainable open-source projects work when the source is honest, the docs match the code, and the development cadence is real — that's the bar we hold ourselves to.

### What providers does TokenPak support?

**Adapters in the current release:** Anthropic, OpenAI (chat, responses and Codex), Google Gemini and xAI Grok, plus a passthrough adapter.

**Tested:** OpenAI SDK, Anthropic SDK and LiteLLM. **First-class integrations:** Claude Code and Codex.

**Other providers:** see the [adapters guide](adapters.md) for the passthrough adapter and for adding your own.

---

## How It Works

### How does TokenPak route requests to providers?

Routing policy is configuration and observe-mode records. Automatic model changes and fallback enforcement are not active by default.

### Does TokenPak support streaming?

The proxy handles streamed responses, and empty streamed responses preserve ordinary accounting observations. If the proxy restarts mid-stream, a retried request gets an explicit `terminally_failed` / `recovery_status` signal instead of a bare connection reset; transparent replay is not implemented.

### How does caching work? Will I get stale responses?

Provider-side prompt-cache hits are recorded separately from TokenPak's own cache. TokenPak's semantic cache is off by default; if you turn it on (`TOKENPAK_SEMANTIC_CACHE`), use it for repeated or batch queries and not for live or dynamic content.

### What about token counting? Is it accurate?

Some counts are estimates. `tokenpak savings --verify` compares TokenPak's existing UTF-8 byte estimator with an independent `cl100k_base` count on a packaged fixture corpus and reports both counts and their divergence; it does not recount stored requests, whose source text is not retained. Session displays label estimates.

---

## Security & Privacy

### Is my data stored? Is it encrypted?

The TokenPak proxy and its local ledger run on your machine. Provider-bound
prompts, responses, and credentials still travel between your client and the
upstream provider you configure; they do not pass through a TokenPak cloud
service. TokenPak sends no telemetry home by default. Request records live in
a local SQLite ledger (`~/.tokenpak/monitor.db` or `~/.tpk/monitor.db` on fresh
installs). Full details are on the
[tokenpak.ai privacy page](https://tokenpak.ai/compliance/privacy).

### How does rate limiting work?

TokenPak supports multiple rate-limiting strategies:

- **Per-provider:** respects each provider's rate limits (e.g., Claude's RPM limits).
- **Per-key:** limits by API key (useful for multi-tenant setups).
- **Per-user:** limits by user ID (requires middleware integration).

Limits are configurable in `config.yaml`. You get clear error messages when limits are exceeded.

### Can I audit requests for compliance?

TokenPak records available request metadata (model, token counts, latency, cost, cache origin) in a local SQLite ledger. Failed writes and missing usage are coverage limits, so treat it as a usage record rather than a compliance audit trail.

---

## Performance & Operations

### What's the performance overhead?

**Proxy internals:** This page does not publish latency figures. Measure the proxy's overhead on your own workload.

**End-to-end latency:** when measured against direct API calls, the proxy adds some overhead due to the network round-trip and connection-pooling differences. This is expected for any local proxy.

**Context:** Measure the effect of explicit context tools on your own workload.

For applications where sub-millisecond response time is critical, either run the proxy on the same machine as your client (recommended), or use the SDK in-process.

### Can I self-host TokenPak?

That's the only way to run TokenPak. You install the OSS package locally:

- **pip:** `pip install tokenpak && tokenpak start`
- **Docker:** build the image from the repository with `docker build -t tokenpak .` (see the [Docker guide](DOCKER.md))

See the [installation guide](installation.md) for deployment options.

### How do I monitor TokenPak?

TokenPak exposes Prometheus metrics on `/metrics`:

- Request count, latency, error rates
- Token usage by model and provider
- Cache hit/miss rates
- Provider health status

You can scrape this in Prometheus, Datadog, or any metrics platform. Logs are JSON-formatted for easy parsing. The local dashboard (`tokenpak dashboard`) gives you a TUI + web view of the same data.

### What if a provider goes down? How does failover work?

Automatic model changes and fallback enforcement are not active by default; routing policy is configuration and observe-mode records. If the proxy restarts mid-stream, a retried request gets an explicit `terminally_failed` / `recovery_status` signal instead of a bare connection reset; transparent replay is not implemented.

---

## Customization & Integration

### How do I add a custom LLM provider?

TokenPak uses an adapter pattern. See the [adapters guide](adapters.md) for the full guide, but the quick version:

1. Create an adapter class inheriting from `BaseAdapter`.
2. Implement `send_request()` and `count_tokens()`.
3. Register it in `config.yaml`.

A full example with a local Ollama instance is in the docs.

### Can I use TokenPak with my favorite SDK (LangChain, LiteLLM, etc.)?

Tested adapters: OpenAI SDK, Anthropic SDK and LiteLLM. Other SDKs that accept a base-URL override are untested. First-class clients are Claude Code and Codex. Where an SDK accepts a base URL, point it at your local proxy; your API key stays where the SDK already reads it from.

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

Yes — that's what **Spend Guard** does. It ships in the current release as a pre-send circuit breaker:

```bash
tokenpak budget --help
```

Defaults are context-window-percentage based (90% warn / 100% hard stop). Dollar-based rolling caps are opt-in. When a request would exceed the cap, TokenPak returns HTTP 402 with `error.type=tokenpak_spend_guard_blocked` and a clear release directive — instead of letting a runaway agent burn through a budget. Full details in the Spend Guard section of the [configuration docs](configuration.md).

---

## Support & Community

### Where do I report bugs?

[GitHub Issues](https://github.com/tokenpak/tokenpak/issues). Include your OS, Python version, TokenPak version, and reproduction steps. We prioritize crashes and regressions.

### How do I request features?

[GitHub Discussions](https://github.com/tokenpak/tokenpak/discussions) for ideas, or [Issues](https://github.com/tokenpak/tokenpak/issues) if you have a detailed spec.

### How do I contribute?

We welcome bug fixes, docs, adapters, and tests. Fork, make your change, and open a PR. Good first issues are labeled [`good-first-issue`](https://github.com/tokenpak/tokenpak/labels/good-first-issue).

### Is there a Slack/Discord community?

There is no Slack or Discord community. Ask questions or start a conversation in [GitHub Discussions](https://github.com/tokenpak/tokenpak/discussions).
