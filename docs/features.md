---
title: "features"
created: 2026-03-24T19:05:55Z
---
# Feature Matrix

All features are **FREE and open source** under the Apache 2.0 license.

---

## Core Features

| Category | Feature | Status | Notes |
|----------|---------|--------|-------|
| **Core Routing** | Multiple provider adapters | ✅ | 5 adapters built-in |
| | Fallback chains | ✅ | Auto-failover to backup providers |
| | Circuit breaker | ✅ | Recovers from rate limits |
| **Token Management** | Token counting (all providers) | ✅ | Unified across Anthropic, OpenAI, Google |
| | Cost tracking | ✅ | Basic tracking + reporting |
| **Compression** | Deduplication | ✅ | Remove repeated content |
| | Document compression | ✅ | Summarize long docs |
| | Instruction table | ✅ | Compress repetitive instructions |
| **Error Handling** | Normalized error messages | ✅ | Consistent across providers |
| | Automatic retries | ✅ | Exponential backoff, configurable |
| | Error telemetry | ✅ | Log error types and frequency |
| **Observability** | Request/response logging | ✅ | JSON logs, searchable |
| | Token usage reports | ✅ | CSV export, JSON export |
| **Agentic** | Error normalization | ✅ | Convert errors to agent-readable format |
| | Streaming support | ✅ | Handle streaming + non-streaming |
| **Vault Integration** | Document indexing | ✅ | Index local files (.md, .txt, .pdf) |
| | Semantic search | ✅ | Search vault by meaning |
| | Auto-injection | ✅ | Automatically add relevant docs to context |
| | Symbol extraction | ✅ | Extract functions, classes, variables |
| | AST parsing | ✅ | Parse code structure |
| | Chunk optimization | ✅ | Smart chunking for injection |
| | Watcher mode | ✅ | Live re-index on file changes |
| **CLI** | `serve` command | ✅ | Start the proxy |
| | `preview` command | ✅ | Dry-run compression on a file (shows token savings) |
| | `benchmark` command | ✅ | Test compression on a document |
| | `validate` command | ✅ | Validate a TokenPak JSON file against the schema |
| | `report` command | ✅ | Generate usage reports |

---

## Feature Details

### Core Proxy

Provider routing, adapters, tool schema handling, fallback chains, circuit breaker, streaming, passthrough.

TokenPak's primary usage model is to run the local proxy and point your existing provider SDK or tool at it via a base URL — no application code changes required:

```bash
# Start the proxy (default: http://127.0.0.1:8766)
tokenpak serve
```

```python
# Use the standard Anthropic SDK, routed through TokenPak
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Token & Cost Tracking

TokenPak tracks per-request token usage and savings server-side. Inspect them over HTTP or via the CLI:

```bash
curl http://127.0.0.1:8766/stats/last    # most recent request
tokenpak stats                           # registry totals
tokenpak savings                         # tokens and cost saved
```

### Compression

Deduplication, doc compression, instruction table, budget tracking, fidelity tiers

Automatically applied. Semantic equivalence guaranteed.

### Error Handling

Normalized errors, automatic retries with exponential backoff, and circuit breaking are applied transparently by the proxy. When an upstream provider fails repeatedly, the proxy opens a circuit breaker (visible at `GET /circuit-breakers`) and surfaces a consistent JSON error to the client. See the [Error Handling Guide](./error-handling.md).

### Vault Features

Indexing, search, auto-injection, symbol extraction, AST parsing, chunking, watcher, SQLite backend

```yaml
vault:
  enabled: true
  root: "~/my-vault"
  auto_inject: true  # Automatically add relevant docs
```

---

## Installation & Usage

```bash
pip install tokenpak
tokenpak serve
```

---

## Configuration Reference

### Basic config.yaml

```yaml
proxy:
  port: 8766
  host: 127.0.0.1

provider: anthropic
fallback:
  - google
  - openai

compression:
  enabled: true

telemetry:
  enabled: true
  log_file: /tmp/tokenpak.log

vault:
  enabled: true
  root: ~/my-vault
```

---

## Feature Roadmap

These items are on the roadmap and are **not part of the current OSS beta surface** — they are directions, not commitments. For exactly what ships in the beta today, see the [feature overview](index.md).

- Multi-turn conversation history management
- Vision / multimodal support
- Advanced batch processing

> TokenPak already ships deterministic **Prompt Packing** today (see the [feature overview](index.md)); it interoperates with provider-side prompt caching rather than replacing it.

---

## Support & Licensing

**License:** Apache 2.0. Use however you like.

See [README](index.md) for more information.
