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
| | `count` command | ✅ | Count tokens in a file |
| | `compress` command | ✅ | Test compression on a document |
| | `validate` command | ✅ | Check config and connectivity |
| | `report` command | ✅ | Generate usage reports |

---

## Feature Details

### Core Proxy

Provider routing, adapters, tool schema handling, fallback chains, circuit breaker, streaming, passthrough

```python
from tokenpak import Client

# Works out-of-the-box
client = Client(api_key="...", model="claude-opus-4-6")
response = client.messages.create(...)
```

### Token Counting

Accurate token counts across all providers

```python
tokens = client.count_tokens(
    model="claude-opus-4-6",
    messages=[{"role": "user", "content": "..."}]
)
```

### Compression

Deduplication, doc compression, instruction table, budget tracking, fidelity tiers

Automatically applied. Semantic equivalence guaranteed.

### Error Handling

Normalized errors, automatic retries with exponential backoff

```python
# Retries automatically with circuit breaker
response = client.messages.create(...)
# If provider fails, falls back to next in chain
```

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
  port: 8000

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

### Coming Soon
- Multi-turn conversation history management
- Prompt caching integration
- Vision/multimodal support
- Advanced batch processing

---

## Support & Licensing

**License:** Apache 2.0. Use however you like.

See [README](index.md) for more information.
