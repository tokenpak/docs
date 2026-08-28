---
title: TokenPak
rung: 1
audience: Developers evaluating or getting started with TokenPak.
updated: 2026-08-20
status: current
hide:
  - navigation
  - toc
---

# TokenPak

**A local proxy that packs LLM context before it reaches the API, with per-request records of what changed.**

This page is for developers evaluating or getting started with TokenPak.
TokenPak sits between your AI tools and the upstream LLM provider, with its
proxy listening on `127.0.0.1`. It deterministically packages context (Prompt
Packing), routes requests, evaluates configured Spend Guard limits before
provider send, and records request results locally. Provider-bound requests
still travel to the selected upstream provider; TokenPak operates no cloud
relay and requires no application code changes.

!!! note "v1.21.0"
    The commands below, [Quick Start](QUICKSTART.md),
    [extended API reference](api-reference.md), and
    [Docker guide](DOCKER.md) describe TokenPak **v1.21.0**, the currently
    published release on PyPI (`pip install tokenpak`). The separate
    [Installation page](installation.md) retains older-release guidance; use
    the Quick Start for the current setup path. Other pages with explicit
    version pins describe the release line named on that page.

---

## What ships in the OSS beta

- **Prompt Packing pipeline** — deterministic context reduction on real agent workloads; reduction pinned to an agent-style CI fixture (reproduce with `make benchmark-headline`); provider-cached flows show lower incremental gains. Measure your own with `tokenpak savings`.
- **Local proxy on 127.0.0.1** — processing and records stay local; provider-bound
  prompts and credentials are sent to the upstream provider you configure, not
  to a TokenPak cloud service.
- **Spend Guard** — pre-send circuit breaker with rolling caps; blocks runaway requests before they reach the provider and returns a clear release directive.
- **Nine client integrations** — Claude Code, Cursor, Cline, Continue, Aider, Codex CLI, OpenAI SDK, Anthropic SDK, LiteLLM.
- **Savings Ledger + local dashboard** — every request logged to a local SQLite store with causal attribution; TUI + web dashboard.
- **Vault indexing + semantic search** — index your codebase, search without an LLM call.
- **TIP-1.0 protocol contracts** — canonical headers, metadata fields, capability labels, manifest schemas. Conformance gate runnable via `tokenpak doctor --conformance`.
- **Pak recall (read-only)** — storage, FTS, `tokenpak pak inspect`. Scoring and assembly are not part of the OSS beta.
- **Three built-in setup profiles and 50+ compression recipes** — minimal, balanced, and aggressive profiles plus customizable packaged YAML recipes.
- **Session economics trip computer** — a deterministic spent/burn/binding-runway/guard-state summary built only from completed local ledger rows, on `tokenpak status`, the dashboard, and an MCP tool. Coverage-tracked calibrated forecasts fill in as a model×effort cell earns enough history; cold cells report an explicit `learning` state rather than a guess.

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
| [Installation](installation.md)            | Older-release installation guidance; use the Quick Start for v1.21.0 |
| [Quick Start](QUICKSTART.md)               | Setup wizard, client integration, first savings in 5 minutes |
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
| [Client Guides](guides/claude-code.md)     | Per-client integration walkthroughs (Claude Code, Cursor, Cline, Continue, Aider, Codex CLI, Gemini CLI, OpenAI/Anthropic SDK) |

---

## Source and package

- **GitHub**: [github.com/tokenpak/tokenpak](https://github.com/tokenpak/tokenpak)
- **PyPI**: [pypi.org/project/tokenpak](https://pypi.org/project/tokenpak)
- **License**: Apache 2.0
