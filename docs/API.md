# TokenPak API Reference

**Complete reference for TokenPak SDK adapters and the local proxy usage pattern.**

---

## Quick Navigation

| Use Case | Class | Import |
|----------|-------|--------|
| Anthropic SDK | `AnthropicAdapter` | `from tokenpak.sdk import AnthropicAdapter` |
| OpenAI SDK | `OpenAIAdapter` | `from tokenpak.sdk import OpenAIAdapter` |
| LangChain | `LangChainAdapter` | `from tokenpak.sdk import LangChainAdapter` |
| LiteLLM | `LiteLLMAdapter` | `from tokenpak.sdk import LiteLLMAdapter` |
| Adapter base + exceptions | `TokenPakAdapter` | `from tokenpak.sdk.base import TokenPakAdapter` |

---

## Primary Usage Pattern — Point Your Existing SDK at the Proxy

The most common way to use TokenPak is to run the local proxy and point your **existing** provider SDK or tool at it via a base URL. No code changes to your provider client are required beyond the base URL.

```bash
# Start the proxy (default: http://127.0.0.1:8766)
tokenpak serve
```

```bash
# Point an existing tool/SDK at the proxy
export ANTHROPIC_BASE_URL=http://127.0.0.1:8766
export OPENAI_BASE_URL=http://127.0.0.1:8766/v1
```

```python
# Using the standard Anthropic SDK, routed through TokenPak
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)
print(response.content[0].text)
```

The proxy transparently applies compression and context handling, then forwards to the upstream provider.

---

## SDK Adapters

The `tokenpak.sdk` adapter layer provides a thin, uniform wrapper around the proxy for callers that prefer a plain-dict request/response interface. All adapters share the `TokenPakAdapter` base contract:

- `prepare_request(request: dict) -> dict` — Validate and normalize the request
- `send(prepared: dict) -> dict` — POST to the proxy, return the raw response
- `parse_response(response: dict) -> dict` — Convert to provider-native format
- `extract_tokens(response: dict) -> dict` — Extract token-usage counts
- `call(request: dict) -> dict` — Convenience: `prepare_request` → `send` → `parse_response`

**Constructor parameters** (all adapters):

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | str | Yes | — | Proxy URL, e.g. `http://127.0.0.1:8766` |
| `api_key` | str | No | `""` | Provider API key (forwarded to upstream) |
| `timeout_s` | float | No | `120.0` | Request timeout in seconds |

### AnthropicAdapter

Routes requests to `/v1/messages` on the proxy.

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)

response = adapter.call({
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "Explain quantum computing"}
    ],
})

# Extract token usage
tokens = adapter.extract_tokens(response)
print(f"Input: {tokens['input_tokens']}")
print(f"Output: {tokens['output_tokens']}")
```

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
    "messages": [{"role": "user", "content": "Hello"}],
})

tokens = adapter.extract_tokens(response)
```

### LangChainAdapter

Adapter for LangChain integrations.

```python
from tokenpak.sdk import LangChainAdapter

adapter = LangChainAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-...",
)

response = adapter.call({
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hi"}],
})
```

### LiteLLMAdapter

Adapter for LiteLLM-style provider-agnostic routing.

```python
from tokenpak.sdk import LiteLLMAdapter

adapter = LiteLLMAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-...",
)

response = adapter.call({
    "model": "claude-sonnet-4-6",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 512,
})
```

---

## Exceptions

All adapter exceptions derive from `TokenPakAdapterError` and are importable from `tokenpak.sdk.base`.

```
TokenPakAdapterError (base)
├── TokenPakTimeoutError   — proxy did not respond within timeout_s
├── TokenPakConfigError    — missing required fields / bad config
└── TokenPakAuthError      — 401 or 403 from the proxy
```

```python
from tokenpak.sdk.base import (
    TokenPakAdapterError,
    TokenPakTimeoutError,
    TokenPakConfigError,
    TokenPakAuthError,
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

**`TokenPakAdapterError` attributes:**
- `message: str` — Error description
- `status_code: int | None` — HTTP status code, if any
- `raw: Any` — Raw response body, if any

---

## Common Patterns

### Pattern: Extract Token Usage Per Request

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
)

response = adapter.call({
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Summarize this"}],
})

tokens = adapter.extract_tokens(response)
# tokens = {"input_tokens": ..., "output_tokens": ..., "cache_read_input_tokens": ..., ...}
```

### Pattern: Inspect Savings via the Proxy

The proxy tracks savings and exposes them over HTTP. After a request, query the last-request stats:

```bash
curl http://127.0.0.1:8766/stats/last
```

Or via the CLI:

```bash
tokenpak stats
tokenpak savings
```

---

## Type Hints

Common type patterns used across the SDK:

- `Optional[T]` / `T | None` — Value may be `None`
- `dict[str, Any]` — Request and response payloads
- `list[dict]` — Message lists

---

## Getting Help

- **Examples:** See the [`examples/`](https://github.com/tokenpak/tokenpak/tree/main/examples) directory in the repository
- **Tests:** See the [`tests/`](https://github.com/tokenpak/tokenpak/tree/main/tests) directory in the repository
- **Quick start:** See [QUICKSTART.md](./QUICKSTART.md)
- **Issues:** Open a GitHub issue on [tokenpak/tokenpak](https://github.com/tokenpak/tokenpak)

---

**TokenPak v1.13.0** — Licensed under Apache 2.0.
