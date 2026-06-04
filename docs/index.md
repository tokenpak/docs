---
hide:
  - navigation
  - toc
---

# TokenPak

**A local proxy that compresses your LLM context before it hits the API — fewer tokens, lower cost, same results.**

TokenPak sits between your AI tools and the upstream LLM provider, running entirely on `127.0.0.1`. It deterministically packages context (Prompt Packing), routes requests, blocks runaway spend before it hits the wire (Spend Guard), and logs every saving locally. No cloud, no credentials stored, no code changes.

!!! note "OSS beta"
    These docs describe the **OSS beta** of TokenPak (`pip install tokenpak`, currently **v1.7.1**, Apache 2.0). Anything not listed here is not part of the beta surface. See [Known Issues](known-issues.md) for current limitations.

---

## What ships in the OSS beta

- **Prompt Packing pipeline** — deterministic context reduction; ≥30% floor pinned in CI on an agent-style fixture, 90%+ routinely observed on direct-API / CLI / uncached workloads. Provider-cached flows (Claude Code) show lower incremental gains.
- **Local proxy on 127.0.0.1** — byte-preserved passthrough; your prompts and credentials never leave your machine.
- **Spend Guard** — pre-send circuit breaker with rolling caps; blocks runaway requests before they reach the provider and returns a clear release directive.
- **Nine client integrations** — Claude Code, Cursor, Cline, Continue, Aider, OpenAI SDK, Anthropic SDK, LiteLLM, Codex.
- **Savings Ledger + local dashboard** — every request logged to a local SQLite store with causal attribution; TUI + web dashboard.
- **Vault indexing + semantic search** — index your codebase, search without an LLM call.
- **TIP-1.0 protocol contracts** — canonical headers, metadata fields, capability labels, manifest schemas. Conformance gate runnable via `tokenpak doctor --conformance`.
- **Pak recall (read-only)** — storage, FTS, `tokenpak pak inspect`. Scoring and assembly are not part of the OSS beta.
- **50 built-in compression profiles** — YAML, customizable.

---

## Quick start

```bash
pip install tokenpak
tokenpak setup
# Then point your client at http://127.0.0.1:8766
```

→ [Full installation guide](installation.md)
→ [5-minute Quick Start](QUICKSTART.md)

---

## Documentation map

| Section | What it covers |
|---------|-----------------|
| [Installation](installation.md)            | `pip install`, system requirements, first run |
| [Quick Start](QUICKSTART.md)               | Setup wizard, client integration, first savings in 5 minutes |
| [Configuration](configuration.md)          | All configuration options |
| [Environment Variables](env-vars.md)       | Complete `TOKENPAK_*` reference |
| [CLI Reference](cli-reference.md)          | Every verb, flag, and exit code (auto-generated) |
| [Architecture](architecture.md)            | Three planes, 18 subsystems, proxy-centered design |
| [Savings](SAVINGS.md)                      | How TokenPak attributes savings causally |
| [Security](SECURITY.md)                    | Auth tokens, TLS, audit logging, data privacy |
| [Troubleshooting](troubleshooting.md)      | Common symptoms and fixes that work |
| [Known Issues](known-issues.md)            | Current OSS-beta limitations |
| [FAQ](faq.md)                              | General questions |
| [Recall overview](recall/index.md)         | Paks, reason codes, risk flags — the OSS data plane |
| [Client Guides](guides/claude-code.md)     | Per-client integration walkthroughs (Claude Code, Cursor, Cline, Continue, Aider, Codex CLI, Gemini CLI, OpenAI/Anthropic SDK) |

---

## Source + package

- **GitHub**: [github.com/tokenpak/tokenpak](https://github.com/tokenpak/tokenpak)
- **PyPI**: [pypi.org/project/tokenpak](https://pypi.org/project/tokenpak)
- **License**: Apache 2.0
