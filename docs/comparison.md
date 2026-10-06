---
title: How TokenPak fits with gateways and observability tools
rung: 2
audience: Developers who already run an LLM gateway or observability tool, such as LiteLLM, and want to know where TokenPak fits.
updated: 2026-10-06
status: current
---

# How TokenPak fits with gateways and observability tools

TokenPak is a local proxy for coding agents that records each request and shows how far the session can go: measured usage, estimated cost, burn and runway. It adds request records, session economics and Spend Guard, and it runs alongside gateways and observability tools such as LiteLLM; it does not replace them.

This page describes TokenPak only. For what any other project offers, read that project's own documentation.

---

## TokenPak at a glance

| Feature | TokenPak |
|---------|----------|
| **Self-hosted** | ✅ Yes, runs locally on `127.0.0.1` |
| **Open source** | ✅ Yes (Apache 2.0 core); Pro is a separate, proprietary package |
| **Provider adapters** | Anthropic, OpenAI (chat, responses and Codex), Google Gemini, xAI Grok, plus a passthrough adapter |
| **Vault compression** | ⚠️ Explicit tools only (not applied to default requests) |
| **Token counting accuracy** | ⚠️ Measured usage; estimated cost; some counts are estimates |
| **Cost tracking per-request** | ✅ Yes |
| **Streaming support** | ✅ Full SSE |
| **Python SDK** | ✅ Yes |
| **JavaScript/TypeScript SDK** | ⚠️ HTTP client only |
| **Docker support** | ⚠️ Build the image from the repository (see the [Docker guide](DOCKER.md)) |
| **Proxy overhead** | Designed for minimal local overhead |
| **Automatic failover** | ⚠️ Not active by default (observe-mode routing records) |
| **Added TokenPak cloud service** | None; requests go to your chosen provider |

---

## Where TokenPak fits

**Strengths:**
- **Short setup** — `python -m pip install tokenpak`, then `tokenpak serve`; the reference path targets five minutes to a first measured receipt
- **Session trip computer** — Measured usage, estimated cost, burn and runway, on by default in the Claude Code footer and the Codex pane and in `tokenpak status`; forecasts are ranges, not guarantees, and appear only once a model has enough local history
- **Explicit context tools** — Explicit compression operations can reduce eligible content. Vault indexing supports search. The default proxy preserves conversation turns, so a forwarded request can report zero tokens saved.
- **No added cloud service** — Requests go to the provider you already use, credentials stay in your existing client and provider flow, and TokenPak does not persist them
- **Lightweight proxy** — Designed to add minimal overhead in front of your providers
- **Apache 2.0 licensed core** — Permissive open source; TokenPak Pro is proprietary
- **Cost tracking** — Per model, per session and per agent, in a local SQLite store

**Trade-offs:**
- A fixed set of built-in provider adapters: Anthropic, OpenAI, Google Gemini, xAI Grok and passthrough
- A local dashboard and `tokenpak status`, not a hosted observability platform
- Automatic failover and model changes are not active by default
- Smaller ecosystem and community

**Best for:**
- Developers and tech leads running long coding-agent sessions in Claude Code or Codex who want to see what a session has used, what finishing will likely cost, and how far it can go.
- Projects with **Anthropic + OpenAI + Gemini** as primary providers
- Developers who want to **run locally** with no TokenPak cloud service
- Applications where **keeping proxy overhead low** is a priority

**When NOT to use TokenPak:**
- If you need to route across many providers, use a gateway built for that and run TokenPak beside it
- If you need a hosted observability platform with team dashboards, TokenPak's local dashboard and `tokenpak status` are not that
- If you need a hosted service (hosted services remain deferred)

---

## Run TokenPak beside a gateway

TokenPak adds request records, session economics and Spend Guard. It does not replace a gateway or an observability tool, so you can run both. LiteLLM is a tested adapter; see the [LiteLLM guide](adapters/litellm.md) for the integration patterns. For what a gateway or observability tool offers, see that project's own documentation.

---

## What TokenPak focuses on

1. **Session Trip Computer** — Measured usage, estimated cost, burn and runway for a coding-agent session, on by default in the Claude Code footer and the Codex pane and in `tokenpak status`. Forecasts are ranges, not guarantees, and appear only once a model has enough local history.

2. **Measured Receipts** — Each request is recorded, and the first request gives you a measured receipt. A forwarded request can truthfully report zero tokens saved.

3. **No Added Cloud Service** — Requests go to the provider you already use, credentials stay in your existing client and provider flow, and TokenPak does not persist them.

4. **Short Setup** — `python -m pip install tokenpak`, then `tokenpak serve`; cost records are kept in a local SQLite store.

5. **Lightweight by Design** — A minimal proxy layer intended to add little overhead in front of your providers. Receipt-backed performance figures will publish once TokenPak's benchmark suite produces a validated run.

---

## Cost

Provider charges apply; TokenPak adds no cloud service. TokenPak records usage and estimated cost. Provider cache reuse is distinct from TokenPak context reduction; inspect attribution with `tokenpak status --tip-cache`.

Actual cost impact depends on your traffic and how much repeated context your workload contains. The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved. Receipt-backed savings figures will publish once TokenPak's benchmark suite produces a validated run.

---

## Integration example

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

---

## Summary

**TokenPak** is built for developers and tech leads running long coding-agent sessions who want to see usage, cost and runway. It adds no cloud service, and its cost tracking is stored in local SQLite. If you need multi-provider routing at scale, observability dashboards or a hosted service, use a tool built for that and run TokenPak beside it.

---

**Questions?** Open an issue on [TokenPak's GitHub](https://github.com/tokenpak/tokenpak) or check the [FAQ](faq.md).
