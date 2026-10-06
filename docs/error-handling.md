---
title: "error-handling"
created: 2026-03-24T19:05:55Z
---
# Error Handling & Troubleshooting

TokenPak returns normalized error responses. Automatic retries and provider fallback are not verified against the current release, and fallback is not active by default.

---

## Common Errors & Solutions

### 1. Connection Refused (Proxy Not Running)

**Error Message:**
```
ConnectionRefusedError: [Errno 111] Connection refused
Failed to connect to http://127.0.0.1:8766
```

**Cause:** The TokenPak proxy server is not running.

**Solution:**
```bash
# Start the proxy
tokenpak serve

# (in another terminal)
python your_script.py
```

**Prevention:** Keep the proxy running in a background process or systemd service.

---

### 2. Authentication Failed (Invalid API Key)

**Error Message:**
```
AuthenticationError: Invalid API key for provider: anthropic
Check your ANTHROPIC_API_KEY environment variable
```

**Cause:** Missing or incorrect API key.

**Solution:**
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set the key
export ANTHROPIC_API_KEY="sk-ant-..."

# Restart the proxy
tokenpak serve
```

**Prevention:**
- Use a `.env` file (see [Installation](./installation.md))
- Check key format (should start with `sk-ant-`, `sk-`, or `AIza-`)
- Rotate expired keys immediately

---

### 3. Rate Limit Exceeded

**Error Message:**
```
RateLimitError: Rate limit exceeded (429)
Retry-After: 60
```

**Cause:** Too many requests to the provider in a short time.

**Solution:**

Handle rate limits in your client. When a request is rate-limited, the proxy returns a `429` with a `rate_limit_exceeded` error body. With the TokenPak SDK adapter, this surfaces as a `TokenPakAdapterError` carrying `status_code == 429`:

```python
import time
from tokenpak.sdk import AnthropicAdapter
from tokenpak.sdk.base import TokenPakAdapterError

adapter = AnthropicAdapter(base_url="http://127.0.0.1:8766", api_key="sk-ant-...")
request = {"model": "claude-opus-4-8", "max_tokens": 100,
           "messages": [{"role": "user", "content": "Hello"}]}

try:
    response = adapter.call(request)
except TokenPakAdapterError as e:
    if e.status_code == 429:
        print("Rate limited. Waiting 60s...")
        time.sleep(60)
        response = adapter.call(request)
    else:
        raise
```

**Prevention:**
- Implement request batching (fewer, larger requests)
- Monitor your request frequency

---

### 4. Model Not Found

**Cause:** Using a model name that the upstream provider doesn't support. The proxy forwards the request and the upstream provider rejects it — the error is passed back to the client as a `4xx` with the provider's message.

**Solution:** Use a valid model name for the target provider. The proxy lists the models it knows about at `GET /v1/models`:

```bash
curl http://127.0.0.1:8766/v1/models
```

**Common Model Names:**

| Provider | Models |
|----------|--------|
| Anthropic | `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5` |
| OpenAI | `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo` |
| Google | `gemini-1.5-pro`, `gemini-1.5-flash` |

**Prevention:** Hardcode model names; don't accept user input directly.

---

### 5. Provider Timeout

**Cause:** The upstream provider took too long to respond. The TokenPak SDK adapter raises `TokenPakTimeoutError` when the proxy does not respond within `timeout_s`.

**Solution (Manual):**
```python
from tokenpak.sdk import AnthropicAdapter
from tokenpak.sdk.base import TokenPakTimeoutError

adapter = AnthropicAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
    timeout_s=60.0,  # 60 second timeout
)

try:
    response = adapter.call(request)
except TokenPakTimeoutError:
    print("Proxy/upstream timed out — retry or report the failure")
```

**Prevention:**
- Set reasonable timeouts (`timeout_s`)
- Monitor provider status

---

### 6. Request Too Large

**Cause:** Request exceeds the target model's context window. The upstream provider rejects oversized requests; the error is passed back through the proxy.

**Solution:**
```python
# Option 1: Reduce message size — keep only relevant context
short_context = "Summary of relevant context only..."

# Option 2: Use an explicit compression operation on eligible context
#   (the default proxy preserves conversation turns; see the compression tuning guide)

# Option 3: Split into multiple smaller requests
```

**Prevention:**
- Use explicit compression on eligible content (the default proxy preserves conversation turns)
- Use vault context injection selectively
- Preview compression savings on a file with `tokenpak preview <file>`

---

### 7. Invalid Configuration

**Error Message:**
```
ConfigError: Invalid config.yaml syntax at line 5:
  compression.enabled must be a boolean, got 'yes'
```

**Cause:** Malformed YAML or invalid option.

**Solution:**
```yaml
# Wrong
compression:
  enabled: yes  # ❌ Should be true/false

# Right
compression:
  enabled: true  # ✅
```

**Validation:**
```bash
# Validate config before starting
tokenpak config validate

# Shows all errors
```

**Prevention:**
- Use YAML validator: https://yamllint.com/
- Check indentation (spaces, not tabs)
- Refer to [Installation guide](./installation.md) for examples

---

## Fallback Chains & Circuit Breaker

> **Not verified / not active by default.** Automatic provider fallback and
> circuit-breaker enforcement are not active by default. Routing policy is
> configuration and observe-mode records; automatic model changes and fallback
> enforcement have not been verified against the current release. The material
> below describes the intended configuration shape, not default behavior.

### How It Works (configuration shape, not active by default)

```yaml
provider: anthropic
fallback:
  - google      # Try if Anthropic fails
  - openai      # Try if Google fails
```

**Intended request flow when fallback is enabled:**
```
1. Try Anthropic
   ├─ Success? ✅ Return response
   ├─ Timeout? → Try Google
   ├─ Rate limit? → Wait then retry
   └─ Permanent error? → Try Google

2. Try Google
   ├─ Success? ✅ Return response
   └─ Fail? → Try OpenAI

3. Try OpenAI
   ├─ Success? ✅ Return response
   └─ Fail? → Return error to client
```

### Circuit Breaker

The circuit breaker is designed to open when a provider fails repeatedly, to limit cascading failures. It is not verified against the current release, and the thresholds and timings below are illustrative, not documented defaults:

```
State: CLOSED (normal operation)
  └─ 3 failures in 60 seconds → OPEN

State: OPEN (provider is down)
  └─ Skip to fallback provider
  └─ After 300 seconds → HALF_OPEN

State: HALF_OPEN (testing recovery)
  └─ Try 1 request
  ├─ Success? → CLOSED
  └─ Fail? → OPEN (restart 300s timer)
```

### Configuration

```yaml
fallback:
  - anthropic
  - google
  - openai

circuit_breaker:
  failure_threshold: 3      # Open after 3 failures
  recovery_timeout: 300     # Reset after 5 minutes
  half_open_requests: 1     # Test 1 request in half-open
```

---

## Monitoring & Debugging

### Enable Debug Logging

```bash
# Detailed logs
TOKENPAK_LOG_LEVEL=DEBUG tokenpak serve

# Write to file
tokenpak serve --log-file /tmp/tokenpak.log
```

### Check Proxy Status

```bash
# Health check endpoint
curl http://127.0.0.1:8766/health

# Circuit breaker / degradation state
curl http://127.0.0.1:8766/circuit-breakers
curl http://127.0.0.1:8766/degradation
```

### Inspect Recent Requests

```bash
# Stats for the most recent request
curl http://127.0.0.1:8766/stats/last

# Full pipeline trace of the last request
curl http://127.0.0.1:8766/trace/last

# All stored pipeline traces
curl http://127.0.0.1:8766/traces

# Export the request ledger as CSV
curl http://127.0.0.1:8766/v1/export/csv
```

### Test Proxy Connectivity

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(base_url="http://127.0.0.1:8766", api_key="sk-ant-...")

try:
    response = adapter.call({
        "model": "claude-opus-4-8",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}],
    })
    print("✅ Reached upstream via the proxy")
except Exception as e:
    print(f"❌ Request failed: {e}")
```

---

## Error Types Reference

### Proxy HTTP Error Types

The proxy returns errors as a JSON object `{"error": {"type": ..., "message": ...}}`. Common types:

| HTTP Status | `error.type` | Cause |
|-------------|--------------|-------|
| 400 | `bad_request` | Malformed request body |
| 401 | `unauthorized` | Missing or invalid `X-TokenPak-Key` |
| 403 | `forbidden` | Operation not allowed from this IP |
| 404 | `not_found` | Unknown endpoint path |
| 429 | `rate_limit_exceeded` | Too many requests from this IP |
| 500 | `internal_error` | Proxy-side error |
| 503 | `circuit_open` | Upstream provider circuit breaker open |
| 503 | `upstream_unreachable` | Cannot reach upstream provider |

### Core Exception Classes (proxy / core)

Raised internally by the proxy and core library. Base class: `TokenPakError`.

| Exception | Cause |
|-----------|-------|
| `AuthenticationError` / `InvalidAPIKeyError` / `MissingAPIKeyError` | API key invalid or absent |
| `RateLimitError` | Upstream rate limit hit |
| `UpstreamError` | Upstream provider returned an error |
| `CircuitOpenError` | Provider circuit breaker is open |
| `SpendGuardBlocked` | Spend guard blocked the request |
| `ProxyError` | Generic proxy-side failure |
| `ConfigError` / `ConfigValidationError` | Invalid configuration |
| `CacheError` | Cache subsystem failure |
| `NetworkConnectionError` / `ProviderConnectionError` | Network/connection failure |
| `PortInUseError` | Configured port already in use |

### SDK Adapter Exceptions

Raised by the `tokenpak.sdk` adapters. Base class: `TokenPakAdapterError` (import from `tokenpak.sdk.base`).

| Exception | Cause |
|-----------|-------|
| `TokenPakTimeoutError` | Proxy did not respond within `timeout_s` |
| `TokenPakConfigError` | Missing required fields / bad config |
| `TokenPakAuthError` | 401 or 403 from the proxy |

### Network Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionRefusedError` | Proxy not running | Start `tokenpak serve` |
| `ConnectionError` | Network unreachable | Check internet connection |
| `SSLError` | Certificate validation failed | Check CA certificates |

---

## Best Practices

### 1. Handle upstream errors in your client

Set timeouts and handle upstream errors in your client; provider fallback is not active by default.

### 2. Wrap Requests in Try-Catch

```python
from tokenpak.sdk.base import (
    TokenPakAdapterError,
    TokenPakTimeoutError,
    TokenPakAuthError,
)

try:
    response = adapter.call(request)
except TokenPakTimeoutError:
    # Handle timeout
    pass
except TokenPakAuthError:
    # Handle auth error
    pass
except TokenPakAdapterError as e:
    # Handle other adapter errors (e.status_code carries the HTTP status)
    logger.error(f"Adapter error: {e}")
```

### 3. Implement Exponential Backoff

Automatic proxy retries are not verified against the current release. For client-side retries:

```python
import time
from tokenpak.sdk.base import TokenPakAdapterError

def call_with_backoff(fn, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return fn()
        except TokenPakAdapterError as e:
            if e.status_code != 429:
                raise
            wait = 2 ** attempt  # 1, 2, 4 seconds
            print(f"Attempt {attempt + 1} rate-limited. Waiting {wait}s...")
            time.sleep(wait)
    raise Exception("All attempts failed")
```

### 4. Preview Compression Before Sending

```bash
# Dry-run compression on a file to estimate token savings
tokenpak preview prompt.txt
```

### 5. Set Timeouts

```python
from tokenpak.sdk import AnthropicAdapter

adapter = AnthropicAdapter(
    base_url="http://127.0.0.1:8766",
    api_key="sk-ant-...",
    timeout_s=30.0,  # 30 second timeout
)
```

---

## Getting Help

- **Question?** Check this guide or the [FAQ](faq.md)
- **Bug?** Open an issue on [GitHub](https://github.com/tokenpak/tokenpak)

---

## Next Steps

- **Monitoring:** See [Observability Guide](./observability.md)
- **Performance:** Check [Feature Matrix](./features.md) for optimization tips
- **Adapters:** See [Adapter Reference](./adapters.md) for provider-specific notes
