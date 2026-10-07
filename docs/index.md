---
title: TokenPak
rung: 1
audience: Developers evaluating or getting started with TokenPak.
updated: 2026-10-07
status: current
hide:
  - navigation
  - toc
---

# TokenPak

**TokenPak is the open logistics layer for AI context.**

TokenPak is a local proxy for coding agents that records each request and shows how far the session can go: measured usage, estimated cost, burn and runway.

**Know how far your agent can go.**

- **Today (release 1.30.2):** request records and receipts; the session trip
  computer (measured usage, estimated cost, burn and runway; forecasts are
  ranges, not guarantees, and appear only once a model has enough local
  history), on by default in the Claude Code footer and the Codex pane from
  1.27.0 and in `tokenpak status`; Spend Guard limits; and explicit context
  tools. Pro, a separate licensed package, adds stay-versus-fresh session
  comparisons with measurements and an explicit confirm or decline. There is no
  self-service purchase; write to hello@tokenpak.ai about access.
- **Planned:** calibrated forecasts for more model and effort combinations; Pro
  reroute recommendations once calibration evidence exists; and any automation
  later, gated separately.

**Who it's for.** Developers and tech leads running long coding-agent sessions
in Claude Code or Codex who want to see what a session has used, what finishing
will likely cost, and how far it can go.

This page is for developers evaluating or getting started with TokenPak.
TokenPak sits between your AI tools and the upstream LLM provider, with its
proxy listening on `127.0.0.1`. The default proxy preserves conversation turns,
evaluates configured Spend Guard limits before provider send, and records
request results locally. Explicit compression operations can reduce eligible
content; the default path does not promise automatic token savings. Provider-bound requests
still travel to the selected upstream provider; TokenPak operates no cloud
relay and requires no application code changes.

!!! note "v1.30.2"
    The commands below, [Quick Start](QUICKSTART.md),
    [extended API reference](api-reference.md), and
    [Docker guide](DOCKER.md) describe TokenPak **v1.30.2**, the currently
    published release on PyPI (`pip install tokenpak`). The separate
    [Installation page](installation.md) retains older-release guidance; use
    the Quick Start for the current setup path. See the
    [1.30.2 upgrade guide](upgrading.md) for the license fixes and dependency
    advice. If you use Pro, read it before upgrading: Pro 0.5.2 supports OSS
    only through 1.30.1. Other pages with explicit version pins describe the
    release line named on that page.

---

## What ships in the OSS beta

- **Context tools and truthful receipts** — explicit compression operations can
  reduce eligible content. Role-bearing conversation history remains intact;
  byte-preserved proxy requests report zero product-attributed reduction. Use
  [measurement methodology](measurement-methodology.md) to interpret savings
  and compare counting methods.
- **Local proxy on 127.0.0.1** — processing and records stay local; provider-bound
  prompts and credentials are sent to the upstream provider you configure, not
  to a TokenPak cloud service.
- **Spend Guard** — pre-send circuit breaker with rolling caps; blocks runaway requests before they reach the provider and returns a clear release directive.
- **Client integrations** — tested SDK adapters: OpenAI SDK, Anthropic SDK and
  LiteLLM; first-class integrations: Claude Code and Codex. Cursor, Cline,
  Continue and Aider are compatibility targets, not yet independently verified.
- **Savings Ledger + local dashboard** — every request logged to a local SQLite store with causal attribution; TUI + web dashboard.
- **Vault indexing + semantic search** — index your codebase, search without an LLM call.
- **TIP-1.0 protocol contracts** — canonical headers, metadata fields, capability labels, manifest schemas. Conformance gate runnable via `tokenpak doctor --conformance`.
- **Pak recall (read-only)** — storage, FTS, `tokenpak pak inspect`. Scoring and assembly are not part of the OSS beta.
- **Three built-in setup profiles and packaged compression recipes** — minimal, balanced, and aggressive profiles plus customizable packaged YAML recipes.
- **Companion forecast footer** — visible by default in interactive Claude Code and Codex launches. See [terminal forecasts](companion-session-forecast.md) for prerequisites, estimates and opt-out settings.
- **Session economics trip computer** — a deterministic spent/burn/binding-runway/guard-state summary built only from completed local ledger rows, on `tokenpak status`, the dashboard, and an MCP tool. Forecasts are estimates shown as ranges, not guarantees; a model and effort combination reports an explicit `learning` state until it has enough local history.

---

## Quick start

```bash
pip install tokenpak
tokenpak setup --start
# Then point your client at http://127.0.0.1:8766
```

→ [5-minute Quick Start](QUICKSTART.md)
→ [Older-release installation guide](installation.md)

---

## Documentation map

| Section | What it covers |
|---------|-----------------|
| [Installation](installation.md)            | Older-release installation guidance; use the Quick Start for v1.30.2 |
| [Quick Start](QUICKSTART.md)               | Setup wizard, client integration, first request receipt, including zero savings |
| [Configuration](configuration.md)          | How configuration works (env vars + YAML, precedence) |
| [Environment Variables](env-vars.md)       | Complete `TOKENPAK_*` reference |
| [CLI Reference](cli-reference.md)          | Every verb, flag, and exit code (auto-generated) |
| [Architecture](architecture.md)            | Three planes, modular subsystems, proxy-centered design |
| [Savings](SAVINGS.md)                      | How TokenPak attributes savings causally |
| [Security](SECURITY.md)                    | Auth tokens, TLS, audit logging, data privacy |
| [Troubleshooting](troubleshooting.md)      | Common symptoms and fixes that work |
| [Known Limitations](KNOWN_LIMITATIONS.md)  | Current OSS-beta limitations, intentional-vs-bug status, and workarounds |
| [FAQ](faq.md)                              | General questions |
| [Recall overview](recall/index.md)         | Paks, reason codes, risk flags — the OSS data plane |
| [Client Guides](guides/claude-code.md)     | Per-client integration walkthroughs (Claude Code, Codex CLI, Gemini CLI, OpenAI/Anthropic SDK); Cursor, Cline, Continue and Aider are compatibility targets, not yet independently verified |

---

## Source and package

- **GitHub**: [github.com/tokenpak/tokenpak](https://github.com/tokenpak/tokenpak)
- **PyPI**: [pypi.org/project/tokenpak](https://pypi.org/project/tokenpak)
- **License**: Apache 2.0
