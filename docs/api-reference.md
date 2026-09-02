---
title: TokenPak API reference
rung: 3
audience: Developers integrating with the TokenPak HTTP API, adapters, or CLI.
updated: 2026-08-20
status: current
---

# TokenPak API reference

This reference is for developers integrating with the TokenPak proxy HTTP API,
SDK adapters, or CLI. It covers the v1.23.0 surface described below.

---

## Table of contents

1. [Proxy HTTP API](#proxy-http-api)
   - [Authentication](#authentication)
   - [GET endpoints](#get-endpoints)
   - [POST endpoints](#post-endpoints)
   - [Error responses](#error-responses)
2. [SDK adapters](#sdk-adapters)
   - [Base adapter (TokenPakAdapter)](#base-adapter-tokenpakadapter)
   - [AnthropicAdapter](#anthropicadapter)
   - [OpenAIAdapter](#openaiadapter)
   - [LangChainAdapter](#langchainadapter)
   - [LiteLLMAdapter](#litellmadapter)
   - [Exception hierarchy](#exception-hierarchy)
3. [CLI commands](#cli-commands)
   - [Proxy lifecycle](#proxy-lifecycle)
   - [Indexing and search](#indexing-and-search)
   - [Monitoring and stats](#monitoring-and-stats)
   - [Diagnostics](#diagnostics)
   - [Config management](#config-management)
   - [Advanced commands](#advanced-commands)
4. [Configuration reference](#configuration-reference)
   - [Environment variables](#environment-variables)
   - [config.yaml](#configuration-file)

---

## Proxy HTTP API

The TokenPak proxy runs on `localhost:8766` by default. It accepts standard HTTP requests and transparently forwards them to upstream providers after applying compression and context injection.

### Authentication

TokenPak allows unauthenticated requests from localhost. A non-localhost bind
is explicit: set `TOKENPAK_BIND_ADDRESS` and configure
`TOKENPAK_PROXY_AUTH_TOKEN` on the server. Remote clients authenticate to the
proxy with the matching Bearer credential:

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `Bearer <proxy-auth-token>` | Required for non-localhost clients; stripped before upstream forwarding |
| `x-api-key` | `<provider-api-key>` | Optional direct provider credential, forwarded upstream |

Non-localhost requests receive `403 Forbidden` when the server has no
`TOKENPAK_PROXY_AUTH_TOKEN`; a missing, malformed, or incorrect Bearer
credential receives `401 Unauthorized`.

---

### GET endpoints

#### `GET /health`

Lightweight, uncached health check. The basic response has one stable top-level
schema and is computed for every request. Add `?deep=true` for bounded provider,
process-memory, and disk diagnostics.

**Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 3600,
  "version": "1.23.0",
  "pid": 4242,
  "requests_total": 142,
  "requests_errors": 2,
  "compression_ratio_avg": 0.4474,
  "is_degraded": false,
  "is_shutting_down": false,
  "in_flight_requests": 0,
  "memory_guard": {
    "enabled": false,
    "state": "disabled",
    "thread_alive": false,
    "callback_policy": "disabled",
    "configuration": {
      "source": "default",
      "mode": "off",
      "plan_sha256": null,
      "managed_config_path": "/home/alex/.tpk/memory-optimization.json",
      "managed_file_present": false,
      "managed_file_ignored": false,
      "triggering_env": [],
      "warning": null
    },
    "callbacks": {
      "compact": false,
      "token": false,
      "semantic": false
    }
  },
  "admission": {
    "limit": 16,
    "available": 16,
    "rejected": 0
  },
  "agent_concurrency": {
    "enabled": true,
    "max_parallel_subagents": 2,
    "effective_cap": 2,
    "degraded_serial": false,
    "in_flight": 0,
    "queued": 0,
    "queue_depth_max": 14,
    "admitted_total": 0,
    "queued_total": 0,
    "rejected_queue_full": 0,
    "rejected_wait_timeout": 0,
    "source": "config"
  },
  "timestamp": "2026-07-24T05:30:00Z",
  "connection_pool": {
    "http2_enabled": true,
    "active_providers": ["api.anthropic.com"],
    "total_requests": 142,
    "reused_connections": 140,
    "new_connections": 2,
    "errors": 2,
    "evicted_clients": 0,
    "reuse_rate": 0.9859,
    "cleanup_pending_close": 0,
    "cleanup_queued": 0,
    "cleanup_in_progress": 0,
    "cleanup_retrying": 0,
    "cleanup_failures_total": 0,
    "cleanup_worker_start_failures_total": 0,
    "cleanup_completed_total": 0,
    "cleanup_oldest_pending_seconds": 0.0,
    "cleanup_workers_alive": 0,
    "client_slots_used": 1,
    "client_slots_max": 64,
    "client_capacity_rejections_total": 0,
    "cleanup_saturated": false,
    "retired_pending_close": 0
  },
  "circuit_breakers": {
    "enabled": true,
    "any_open": false,
    "providers": {
      "anthropic": {
        "state": "closed",
        "failures_in_window": 0,
        "successes_in_window": 0,
        "failure_ratio": 0.0,
        "failure_threshold": 5,
        "min_failure_ratio": 0.5,
        "time_until_probe_seconds": null,
        "total_trips": 0,
        "total_successes": 140,
        "total_failures": 2
      }
    }
  }
}
```

#### `GET /stats`

Current session counters, compilation mode, memory-guard status, and provider-cache
read attribution.

**Response:**
```json
{
  "session": {
    "requests": 142,
    "input_tokens": 380000,
    "sent_input_tokens": 210000,
    "saved_tokens": 170000,
    "protected_tokens": 0,
    "output_tokens": 95000,
    "cost": 0.85,
    "cost_saved": 0.42,
    "errors": 2,
    "start_time": 1711584000.0,
    "cache_read_tokens": 80000,
    "cache_creation_tokens": 15000,
    "cache_read_client": 80000,
    "cache_read_proxy": 0,
    "cache_read_unknown": 0,
    "ingest_entries": 0
  },
  "compilation_mode": "hybrid",
  "memory_guard": {
    "enabled": false,
    "state": "disabled",
    "thread_alive": false,
    "callback_policy": "disabled",
    "configuration": {
      "source": "default",
      "mode": "off",
      "plan_sha256": null,
      "managed_config_path": null,
      "managed_file_present": false,
      "managed_file_ignored": false,
      "triggering_env": [],
      "warning": null
    },
    "callbacks": {
      "compact": false,
      "token": false,
      "semantic": false
    }
  },
  "cache_read_by_origin": {
    "client": 80000,
    "proxy": 0,
    "unknown": 0
  }
}
```

---

#### `GET /stats/last`

Per-request stats for the most recent proxied request.

**Response:**
```json
{
  "request_id": "a1b2c3d4",
  "timestamp": "2026-03-28T16:00:00",
  "model": "claude-sonnet-4-6",
  "input_tokens_raw": 4380,
  "input_tokens_sent": 3140,
  "output_tokens": 512,
  "tokens_saved": 1240,
  "cost_saved": 0.0037,
  "percent_saved": 28.3
}
```

**Error (no requests yet):**
```json
{
  "error": "no_requests",
  "message": "No requests captured yet."
}
```

---

#### `GET /stats/session`

Session aggregate summary with uptime and average savings.

**Response:**
```json
{
  "session_requests": 142,
  "session_total_saved": 0.42,
  "tokens_saved": 170000,
  "tokens_sent": 210000,
  "tokens_raw": 380000,
  "output_tokens": 95000,
  "total_cost": 0.85,
  "uptime_hours": 4.5,
  "errors": 2,
  "avg_savings_pct": 44.7
}
```

---

#### `GET /cache-stats`

Detailed cache hit/miss breakdown.

---

#### `GET /trace/last`

Full pipeline trace for the most recent request (debugging).

**Response:**
```json
{
  "request_id": "a1b2c3d4",
  "timestamp": "16:00:00",
  "model": "claude-sonnet-4-6",
  "input_tokens": 4380,
  "output_tokens": 512,
  "tokens_saved": 1240,
  "cost_saved": 0.0037,
  "total_cost": 0.012,
  "duration_ms": 317.0,
  "stages": [
    {
      "name": "capsule_builder",
      "enabled": true,
      "input_tokens": 4380,
      "output_tokens": 3140,
      "tokens_delta": 1240,
      "duration_ms": 45.0,
      "details": {
        "blocks_capsulized": 2,
        "ratio": 0.7169,
        "skip_reason": null
      }
    }
  ],
  "status": "complete"
}
```

**Error (no traces yet):**
```json
{
  "error": "no_traces"
}
```

---

#### `GET /trace/<request_id>`

Pipeline trace for a specific request by ID.

---

#### `GET /traces`

All stored pipeline traces (up to last N requests).

**Response:**
```json
{
  "traces": [
    {
      "request_id": "a1b2c3d4",
      "timestamp": "16:00:00",
      "model": "claude-sonnet-4-6",
      "input_tokens": 4380,
      "output_tokens": 512,
      "tokens_saved": 1240,
      "cost_saved": 0.0037,
      "total_cost": 0.012,
      "duration_ms": 317,
      "stages": [
        {
          "name": "compaction",
          "enabled": true,
          "input_tokens": 4380,
          "output_tokens": 3140,
          "tokens_delta": 1240,
          "duration_ms": 45,
          "details": {}
        }
      ],
      "status": "complete"
    }
  ],
  "count": 1
}
```

---

#### `GET /metrics`

Prometheus-compatible metrics in text format.

**Content-Type:** `text/plain; version=0.0.4; charset=utf-8`

**Example output:**
```text
# HELP tokenpak_requests_total Total proxied requests
# TYPE tokenpak_requests_total counter
tokenpak_requests_total 142
tokenpak_tokens_input_total 380000
tokenpak_tokens_saved_total 170000
tokenpak_errors_total 2
tokenpak_uptime_seconds 16200
```

---

#### `GET /metrics/dashboard`

Comprehensive dashboard metrics with 8 key metrics in JSON format.

**Response:**
```json
{
  "timestamp": "2026-03-28T16:00:00Z",
  "uptime_seconds": 16200,
  "requests": {
    "total": 142,
    "throughput_req_per_sec": 0.009,
    "24h_window": true
  },
  "latency": {
    "p50_ms": 320.0,
    "p95_ms": 980.0,
    "p99_ms": 1840.0,
    "avg_ms": 415.0,
    "samples": 100
  },
  "models": {
    "claude-sonnet-4-6": { "requests": 100, "input_tokens": 250000, "cost": 0.60 }
  },
  "routing": { "smart_routing_hit_rate": 0.0 },
  "cache": {
    "hit_ratio": 0.42,
    "read_tokens": 85000,
    "creation_tokens": 118000
  },
  "errors": {
    "error_rate": 0.014,
    "error_count": 2,
    "top_failures": { "429": 1, "503": 1 }
  },
  "streaming": { "count": 0, "percentage": 0.0 },
  "window_24h": {
    "input_tokens": 380000,
    "output_tokens": 95000,
    "total_cost": 0.85
  }
}
```

---

#### `GET /dashboard` / `GET /dashboard/<path>`

Serves the built-in HTML monitoring dashboard.

---

### POST endpoints

#### `POST /v1/messages`

Anthropic Messages API — the primary proxy path for Claude models.

TokenPak intercepts this request, applies compression, and forwards to the upstream Anthropic API. The response is transparently passed back.

**Headers:**

| Header | Value | Required |
|--------|-------|----------|
| `Content-Type` | `application/json` | Yes |
| `x-api-key` | `<anthropic-api-key>` | Yes |
| `anthropic-version` | `2023-06-01` | Recommended |

**Request Body:**
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": "Explain quantum entanglement."
    }
  ],
  "system": "You are a helpful physics tutor.",
  "stream": false
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model ID (e.g. `claude-sonnet-4-6`) |
| `messages` | array | Yes | Conversation history — `role` + `content` pairs |
| `max_tokens` | integer | Yes | Maximum tokens in the response |
| `system` | string | No | System prompt |
| `stream` | boolean | No | Enable SSE streaming (default: false) |
| `temperature` | float | No | Sampling temperature (0.0–1.0) |
| `top_p` | float | No | Nucleus sampling threshold |
| `stop_sequences` | array | No | Custom stop strings |
| `tools` | array | No | Tool/function definitions |
| `tool_choice` | object | No | Tool selection policy |

**Response:**
```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Quantum entanglement is..." }
  ],
  "model": "claude-sonnet-4-6",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 3140,
    "output_tokens": 512,
    "cache_read_input_tokens": 1200,
    "cache_creation_input_tokens": 800
  }
}
```

---

#### `POST /v1/messages/session-economics`

Build a versioned session-economics snapshot from completed local request
ledger rows. This endpoint never forwards a provider request.

Supply the stable session identity in `X-Claude-Code-Session-Id` or as
`session_id` in the JSON body. If both are present, they must match. `model` is
an optional hint when the ledger does not identify a model unambiguously.

If neither is supplied, v1.23.0 resolves a default session: an explicit id and
the caller's active-session marker are checked first, and if neither exists
the proxy falls back to the most recent session with at least one completed,
non-empty ledger row. If no defaultable session exists yet (empty ledger, or
no completed rows), the response reports an explicit no-data/unavailable
state rather than inventing a session.

**Request body:**

```json
{
  "session_id": "session-abc",
  "model": "claude-sonnet-4-5"
}
```

**Selected response fields:**

```json
{
  "schema_version": "session-economics/1",
  "as_of": "2026-08-12T00:00:00Z",
  "session": {
    "id": "session-abc",
    "identity_state": "observed",
    "turns_observed": 12,
    "model": {"id": "claude-sonnet-4-5", "effort": "unknown"}
  },
  "runway": {
    "status": "available",
    "turns": 8,
    "binding_constraint": "context_soft",
    "guard_state": "amber"
  },
  "advisory": null
}
```

The full immutable response also includes truth-preserving `facts`, `state`,
and `forecast` objects. Missing measurements use explicit `no_data`,
`unavailable`, or `error` states and `null` values; they are never represented
as measured zero. Runway can be `learning`, `unavailable`, or `error` when the
local facts are insufficient or invalid.

---

#### `POST /v1/chat/completions`

OpenAI Chat Completions API — compatible path for OpenAI SDK clients, LangChain, and LiteLLM.

**Headers:**

| Header | Value | Required |
|--------|-------|----------|
| `Content-Type` | `application/json` | Yes |
| `Authorization` | `Bearer <provider-api-key>` | Yes for localhost direct-key traffic; remote clients use this header for proxy auth and need separate upstream credentials |

**Request Body:**
```json
{
  "model": "gpt-4o",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello!" }
  ],
  "max_tokens": 1024,
  "stream": false
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model ID |
| `messages` | array | Yes | Message list with `role` and `content` |
| `max_tokens` | integer | No | Maximum response tokens |
| `stream` | boolean | No | Enable SSE streaming |
| `temperature` | float | No | Sampling temperature |
| `functions` | array | No | Function/tool definitions (legacy) |
| `tools` | array | No | Tool definitions |

---

#### `POST /ingest`

Accept one JSON payload and return one generated record ID. In v1.23.0, this
compatibility endpoint acknowledges the payload but does not persist or index
its contents.

**Request body:**
```json
{
  "content": "Compatibility payload"
}
```

**Response:**
```json
{
  "status": "ok",
  "ids": ["2bd628a3-8b9b-4ed8-9248-b21c90dcdd4b"]
}
```

---

### Error responses

Error bodies are endpoint-specific. TokenPak-generated application errors are
usually JSON, unsupported paths use the standard HTTP server error response,
and provider passthrough routes can return the upstream provider's status and
body. Clients should branch on the HTTP status and parse the documented
endpoint response instead of assuming one universal error envelope.

---

## SDK adapters

TokenPak provides adapters that route requests through the proxy while preserving the native API shape of each SDK.

### Base adapter: `TokenPakAdapter`

All adapters inherit from `TokenPakAdapter` and implement four lifecycle hooks.

```python
from tokenpak.sdk.base import TokenPakAdapter
```

**Constructor Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | str | Yes | — | Proxy URL, e.g. `http://127.0.0.1:8766` |
| `api_key` | str | Yes | — | Provider API key (forwarded to upstream) |
| `timeout_s` | float | No | `120.0` | Request timeout in seconds |

**Lifecycle Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `prepare_request` | `(request: dict) -> dict` | Validate and normalise request |
| `send` | `(prepared: dict) -> dict` | POST to proxy, return raw response |
| `parse_response` | `(response: dict) -> dict` | Convert to SDK-native format |
| `extract_tokens` | `(response: dict) -> dict` | Extract `{input_tokens, output_tokens, cache_read, cache_write, total}` token counts |

**High-level call method:**

```python
# Convenience: calls prepare_request → send → parse_response
response = adapter.call(request_dict)

# Extract token usage
tokens = adapter.extract_tokens(response)
# tokens = {"input_tokens": 3140, "output_tokens": 512, ...}
```

---

### AnthropicAdapter

Routes requests to `/v1/messages` on the proxy.

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-api03-...",
)

response = adapter.call({
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "What is 2 + 2?"}
    ],
})

print(response["content"][0]["text"])
tokens = adapter.extract_tokens(response)
print(f"Input tokens: {tokens['input_tokens']}")
```

**Proxy Path:** `POST /v1/messages`

**Required Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Claude model ID |
| `messages` | list | Non-empty list of `{role, content}` dicts |
| `max_tokens` | integer | Maximum completion tokens |

**Added Defaults (if not present):**
- `stream` defaults to `false`

**Extra Headers Sent:**
- `anthropic-version: 2023-06-01`

**`extract_tokens` Return:**
```python
{
  "input_tokens": 3140,
  "output_tokens": 512,
  "cache_read": 1200,
  "cache_write": 800,
  "total": 3652
}
```

---

### OpenAIAdapter

Routes requests to `/v1/chat/completions` on the proxy.

```python
from tokenpak.sdk import OpenAIAdapter

adapter = OpenAIAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-...",
)

response = adapter.call({
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": "Hello, world!"}
    ],
})
```

**Proxy Path:** `POST /v1/chat/completions`

**Required Request Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | OpenAI model ID |
| `messages` | list | Non-empty list of `{role, content}` dicts |

---

### LangChainAdapter

Drop-in adapter for LangChain integrations.

```python
from tokenpak.sdk import LangChainAdapter

adapter = LangChainAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)
```

**Constructor Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | str | Yes | — | Proxy URL |
| `api_key` | str | Yes | — | Provider API key |
| `timeout_s` | float | No | `120.0` | Request timeout |

---

### LiteLLMAdapter

Drop-in adapter for LiteLLM integrations.

```python
from tokenpak.sdk import LiteLLMAdapter

adapter = LiteLLMAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)
```

**Constructor Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | str | Yes | — | Proxy URL |
| `api_key` | str | Yes | — | Provider API key |
| `timeout_s` | float | No | `120.0` | Request timeout |

---

### Exception hierarchy

All adapters raise canonical exceptions — never raw `requests` exceptions.

```text
TokenPakAdapterError (base)
├── TokenPakTimeoutError      — proxy did not respond within timeout_s
├── TokenPakConfigError       — missing required fields / bad config
└── TokenPakAuthError         — 401 or 403 from proxy
```

**Usage:**
```python
from tokenpak.sdk.base import (
    TokenPakAdapterError,
    TokenPakTimeoutError,
    TokenPakAuthError,
    TokenPakConfigError,
)

try:
    response = adapter.call(request)
except TokenPakTimeoutError:
    print("Proxy timed out")
except TokenPakAuthError as e:
    print(f"Auth failed: {e} (HTTP {e.status_code})")
except TokenPakConfigError as e:
    print(f"Config error: {e}")
except TokenPakAdapterError as e:
    print(f"Adapter error: {e} (HTTP {e.status_code})")
```

---

## CLI commands

All commands are invoked as `tokenpak <command> [options]`.

### Proxy lifecycle

#### `tokenpak start`

Start the managed background proxy (default: `localhost:8766`).

```bash
tokenpak start                    # Start on default port 8766
tokenpak start --port 9000        # Custom port
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | int | `8766` | Port to listen on |

---

#### `tokenpak stop`

Stop the running proxy process.

```bash
tokenpak stop
```

---

#### `tokenpak restart`

Restart the proxy (stop + start).

```bash
tokenpak restart
```

---

#### `tokenpak logs`

Show recent proxy log output.

```bash
tokenpak logs                # Last 50 lines
tokenpak logs -n 100         # Last 100 lines
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-n`, `--lines` | int | `50` | Number of log lines to show |

---

#### `tokenpak status`

Show system status and recent retry events.

```bash
tokenpak status
```

---

#### `tokenpak version`

Show current versions (proxy, config, CLI).

```bash
tokenpak version
```

---

#### `tokenpak update`

Update TokenPak to latest version from git/PyPI.

```bash
tokenpak update
```

---

### Indexing and search

#### `tokenpak index [directory]`

Index a directory for vault-based context injection.

```bash
tokenpak index ~/your-vault           # Index the vault
tokenpak index ~/your-vault --watch   # Watch and auto-reindex on changes
tokenpak index --status          # Show indexed file count by type
tokenpak index -w 8              # Use 8 parallel workers
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `directory` | path | — | Directory to index (positional) |
| `--status` | flag | off | Show indexed file count by type |
| `--workers`, `-w` | int | `4` | Parallel indexing workers |
| `--watch` | flag | off | Watch for file changes and auto-reindex |
| `--recalibrate` | flag | off | Run worker calibration before indexing |
| `--max-workers` | int | `8` | Worker cap for auto-calibration |

---

#### `tokenpak search <query>`

Search the indexed vault content using BM25.

```bash
tokenpak search "compression budget"
tokenpak search "rate limits" --top 10
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `query` | string | — | Search query (positional) |

---

#### `tokenpak calibrate <directory>`

Calibrate the optimal worker count for parallel indexing on this host.

```bash
tokenpak calibrate ~/your-vault
```

---

### Monitoring and stats

#### `tokenpak stats`

Show registry statistics (request counts, token usage, cost breakdown).

```bash
tokenpak stats
```

---

#### `tokenpak models`

Show per-model usage and efficiency breakdown.

```bash
tokenpak models                      # Summary table
tokenpak models sonnet               # Details for models matching "sonnet"
tokenpak models --raw                # JSON output
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `model` | string | Optional positional model name (partial match) |
| `--raw` | flag | Output as JSON |

---

#### `tokenpak savings`

Show savings summary — tokens and cost saved by compression.

```bash
tokenpak savings
tokenpak savings --days 30
tokenpak savings --json
```

---

#### `tokenpak usage`

Show model usage summary.

```bash
tokenpak usage
```

---

#### `tokenpak compare`

Show before/after cost comparison for the last proxied request.

```bash
tokenpak compare
```

---

#### `tokenpak leaderboard`

Show per-model efficiency ranking (savings rate, cost per token).

```bash
tokenpak leaderboard
```

---

#### `tokenpak report`

Generate a daily savings report.

```bash
tokenpak report
```

---

#### `tokenpak requests`

Live request explorer — browse recent proxied requests interactively.

```bash
tokenpak requests
```

---

#### `tokenpak timeline`

View savings trend over the last 7 or 30 days.

```bash
tokenpak timeline
```

---

#### `tokenpak attribution`

View savings broken down by agent, skill, and model.

```bash
tokenpak attribution
```

---

#### `tokenpak aggregate`

Aggregate request ledger data across multiple machines.

```bash
tokenpak aggregate
```

---

#### `tokenpak monitor`

Start the live monitor dashboard on port 8767.

```bash
tokenpak monitor
tokenpak monitor --port 8768     # Custom port
```

---

#### `tokenpak dashboard`

Real-time health dashboard (TUI) or serve the public web dashboard URL.

```bash
tokenpak dashboard               # TUI view
tokenpak dashboard --public      # Open web dashboard in browser
```

---

#### `tokenpak check-alerts`

Evaluate alert rules and report any health violations.

```bash
tokenpak check-alerts
```

---

### Diagnostics

#### `tokenpak doctor`

Run comprehensive system diagnostics.

```bash
tokenpak doctor
```

Checks:
- Proxy connectivity (port 8766)
- Upstream provider reachability
- API key validity
- Vault index health
- Config file validity

---

#### `tokenpak preview [<text>]`

Preview compression dry-run on a file — shows token savings before sending to API.

```bash
tokenpak preview "Long prompt text"
tokenpak preview --file prompt.txt
```

---

#### `tokenpak debug on|off|status`

Toggle verbose debug logging or check current debug state.

```bash
tokenpak debug on
tokenpak debug off
tokenpak debug status
```

---

#### `tokenpak learn status`

Show learned compression patterns from telemetry.

```bash
tokenpak learn status
```

#### `tokenpak learn reset`

Clear all learned data and reset to baseline.

```bash
tokenpak learn reset
```

---

#### `tokenpak replay`

List, inspect, and re-run captured sessions (zero API cost).

```bash
tokenpak replay list             # List recent captured sessions
tokenpak replay show <id>        # Show full details
tokenpak replay run <id>         # Re-run with different settings
tokenpak replay clear            # Remove all entries
```

---

#### `tokenpak validate <file>`

Validate a TokenPak JSON file against the v1.0 schema.

```bash
tokenpak validate my-config.json
```

---

#### `tokenpak diff`

Show context changes (removed/compressed/retained blocks) for a request.

```bash
tokenpak diff
```

---

#### `tokenpak vault-health`

Vault index health diagnostic and repair.

```bash
tokenpak vault-health            # Check index health
tokenpak vault-health repair     # Rebuild stale vault index
```

---

### Config management

#### `tokenpak setup`

Interactive first-time configuration wizard.

```bash
tokenpak setup
```

---

#### `tokenpak config`

Config management subcommands.

```bash
tokenpak config show             # Show merged config (file + env overrides)
tokenpak config sync             # Sync config from canonical source
tokenpak config pull             # Pull config from git or URL
tokenpak config validate         # Validate config against schema
tokenpak config init             # Create default config.yaml
tokenpak config path             # Print config file path
```

---

#### `tokenpak route`

Manage manual model routing rules.

```bash
tokenpak route list              # List routing rules
tokenpak route add --model "gpt-4*" --target openai/gpt-4o
tokenpak route remove <id>       # Remove a rule
```

---

### Advanced commands

#### `tokenpak serve`

Start monitoring proxy or telemetry ingest server.

```bash
tokenpak serve                   # Standard proxy
tokenpak serve --telemetry       # Telemetry ingest server
tokenpak serve --ingest          # Phase 5A ingest API server
tokenpak serve --workers 2       # Multiple uvicorn workers
```

---

#### `tokenpak benchmark`

Benchmark compression performance.

```bash
tokenpak benchmark               # Built-in sample data
tokenpak benchmark --file prompt.txt
tokenpak benchmark --latency ~/your-vault   # Latency/indexing benchmark
tokenpak benchmark --json        # JSON output
```

---

#### `tokenpak macro`

Manage and run premade and user-defined macros.

```bash
tokenpak macro list              # List all macros
tokenpak macro run <name>        # Run a macro
tokenpak macro create --name daily-check --step 'Check status:tokenpak status'
tokenpak macro show <name>       # Show macro definition
tokenpak macro delete <name>     # Delete a user-defined macro
```

---

#### `tokenpak recipe`

Manage compression recipes (YAML workflow definitions).

```bash
tokenpak recipe create my-recipe # Scaffold a new recipe YAML
tokenpak recipe validate <file>  # Validate recipe against schema
tokenpak recipe test <file>      # Test recipe against sample input
tokenpak recipe benchmark <file> # Benchmark recipe performance
```

---

#### `tokenpak fleet`

Manage and query a multi-machine proxy fleet.

```bash
tokenpak fleet init              # Configure fleet interactively
tokenpak fleet                   # Show fleet health
tokenpak fleet --json            # Show fleet health as JSON
```

---

#### `tokenpak template`

Manage local user prompt templates.

```bash
tokenpak template list
tokenpak template add <name>     # Add or update a template
tokenpak template show <name>    # Display a template
tokenpak template remove <name>  # Delete a template
tokenpak template use <name>     # Expand a template with variables
```

---

#### `tokenpak audit` (Planned)

The `audit` command is a reserved, planned stub in v1.23.0. It does not expose
audit-log subcommands in this release.

---

## Configuration reference

### Environment variables

The proxy resolves configuration through `TOKENPAK_HOME` and the state-bearing
TokenPak home. New installs use `~/.tpk/config.yaml`; existing legacy installs
may continue using `~/.tokenpak/config.yaml`. Environment variables take
precedence.

#### Core settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENPAK_PORT` | `8766` | Proxy listen port |
| `TOKENPAK_BIND_ADDRESS` | `127.0.0.1` | Proxy bind address; set explicitly for non-localhost access |
| `TOKENPAK_PROXY_AUTH_TOKEN` | — | Required server-side token for non-localhost access |
| `TOKENPAK_MODE` | `hybrid` | Compression mode: `strict`, `hybrid`, `aggressive` |
| `TOKENPAK_COMPACT` | `1` | Legacy compatibility value; it does not toggle body compaction on the default HTTP proxy path |
| `TOKENPAK_DB` | `~/.tpk/monitor.db` | SQLite database path for a fresh install; existing legacy stores are still discovered |

#### Compression settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENPAK_COMPACT_MAX_CHARS` | `120` | Maximum chars for compressed text chunks |
| `TOKENPAK_COMPACT_THRESHOLD_TOKENS` | `1500` | Skip compression below this token count |
| `TOKENPAK_COMPACT_CACHE_SIZE` | `2000` | Compression result cache entries |

#### Vault context injection

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENPAK_VAULT_INDEX` | `~/vault/.tokenpak` | Path to vault index directory |
| `TOKENPAK_INJECT_BUDGET` | `4000` | Max tokens to inject from vault per request |
| `TOKENPAK_INJECT_TOP_K` | `5` | Max vault blocks to inject per request |
| `TOKENPAK_INJECT_MIN_SCORE` | `2.0` | Minimum BM25 score to include a block |
| `TOKENPAK_RETRIEVAL_BACKEND` | `json_blocks` | Vault backend: `json_blocks` or `sqlite` |

#### Key management

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Primary Anthropic API key |
| `ANTHROPIC_OAUTH_TOKEN` | — | Rotation key 2 |
| `ANTHROPIC_OAUTH_TOKEN2` | — | Rotation key 3 |
| `TOKENPAK_KEY_ROTATION` | `failover` | Key rotation mode: `failover` or `roundrobin` |
| `TOKENPAK_KEY_COOLDOWN_429` | `60` | Rate-limit cooldown seconds |
| `TOKENPAK_KEY_COOLDOWN_401` | `300` | Invalid-key cooldown seconds |

#### Advanced features

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKENPAK_CAPSULE_BUILDER` | `0` | Enable capsule builder stage (`0` or `1`) |
| `TOKENPAK_CAPSULE_MIN_CHARS` | `400` | Min chars for a block to be capsulised |
| `TOKENPAK_ROUTER_ENABLED` | `true` | Enable smart model router |
| `TOKENPAK_HTTP100_KEEPALIVE` | `0` | Send HTTP 100 Continue before compression |

---

### Configuration file

New-install location: `~/.tpk/config.yaml`. Existing state in
`~/.tokenpak/config.yaml` remains in place until explicitly migrated.

This excerpt uses released configuration keys. Run `tokenpak config init` to
generate the complete file for the installed version.

```yaml
port: 8766
mode: hybrid

compression:
  enabled: true
  max_chars: 120
  threshold_tokens: 1500
  cache_size: 2000

vault:
  index_path: ~/vault/.tokenpak
  inject_budget: 4000
  inject_top_k: 5
  inject_min_score: 2.0
  retrieval_backend: json_blocks

rate_limit_rpm: 60
```

---

*This reference covers TokenPak v1.23.0.*
