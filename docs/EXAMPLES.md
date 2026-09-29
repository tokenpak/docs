---
title: "EXAMPLES"
created: 2026-03-24T19:05:55Z
---
# TokenPak Usage Examples

> Copy-paste ready examples for common TokenPak patterns. The default proxy preserves conversation turns, so a forwarded request can report zero tokens saved.

---

## Example 1: Hello World — Basic Proxy Setup

**Problem:** You want to route your Anthropic API calls through TokenPak to get request records and cost tracking.

**Solution:** Start the proxy, point your client at `localhost:8766` instead of `api.anthropic.com`.

### Setup

```bash
# Install TokenPak
pip install tokenpak

# Start the proxy (default port 8766)
tokenpak serve

# Or with a custom port
TOKENPAK_PORT=8766 tokenpak serve
```

### Drop-in Replacement

```python
import anthropic

# Before (direct to Anthropic)
client = anthropic.Anthropic(api_key="sk-ant-...")

# After (through TokenPak proxy) — ONE LINE CHANGE
client = anthropic.Anthropic(
    api_key="sk-ant-...",
    base_url="http://localhost:8766",
)

# Your existing code works unchanged
message = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain quantum entanglement."}]
)
print(message.content[0].text)
```

### Expected Output

The proxy listens on `127.0.0.1` by default. Run `tokenpak status` to see requests as they are recorded and `tokenpak savings` to inspect recorded usage. A forwarded request can report zero tokens saved.

---

## Example 2: Compression settings

The `TOKENPAK_COMPACT` flag and the `compression.enabled` setting remain accepted compatibility settings, but the built-in default HTTP proxy does not call the legacy body-compaction helper, so they do not change default HTTP request bytes. Explicit compression operations can reduce eligible content; inspect recorded usage with `tokenpak savings`.

---

## Example 3: Vault indexing and context injection

**Problem:** You want project documentation indexed so it can be searched and, if you choose, added to requests as context.

**Solution:** Index your documentation. Automatic context injection is off by default; enabling it is an explicit decision (`TOKENPAK_VAULT_INJECTION`). Injection totals are reported by `tokenpak status` and `GET /stats`.

```bash
# Index your project docs
tokenpak index ~/my-project/docs

# Or point to a custom path
VAULT_INDEX_PATH=~/my-project/.tokenpak tokenpak index ~/my-project/docs

# Rebuild on change
tokenpak index ~/my-project/docs --watch
```

---

## Example 4: Error Handling + Retry Logic

**Problem:** You need robust error handling when the upstream API is rate-limited or unavailable.

**Solution:** Use the circuit breaker information from `/health` to detect provider issues, and implement exponential backoff.

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_tokenpak_session(
    proxy_url: str = "http://localhost:8766",
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> requests.Session:
    """Create a requests Session that routes through TokenPak with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 529],  # 529 = Anthropic overloaded
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    return session


def check_proxy_health(proxy_url: str = "http://localhost:8766") -> dict:
    """Check if proxy and upstream providers are healthy."""
    try:
        r = requests.get(f"{proxy_url}/health", timeout=2)
        data = r.json()
        cb = data.get("circuit_breakers", {})
        if cb.get("any_open"):
            open_providers = [
                name for name, status in cb.get("providers", {}).items()
                if status.get("state") == "open"
            ]
            print(f"⚠️  Circuit breaker OPEN for: {open_providers}")
        return data
    except requests.RequestException:
        return {"status": "unreachable"}


def chat_with_retry(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    proxy_url: str = "http://localhost:8766",
    api_key: str = None,
) -> str:
    """Send a chat message with full retry + health check logic."""
    # Check health before sending
    health = check_proxy_health(proxy_url)
    if health.get("status") not in ("ok", "degraded"):
        raise RuntimeError(f"Proxy unhealthy: {health}")

    session = create_tokenpak_session(proxy_url)

    for attempt in range(3):
        try:
            r = session.post(
                f"{proxy_url}/v1/messages",
                headers={
                    "x-api-key": api_key or "sk-ant-...",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]

        except requests.HTTPError as e:
            if e.response.status_code == 529:
                wait = 2 ** attempt
                print(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/3)")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Max retries exceeded")


# Usage
if __name__ == "__main__":
    response = chat_with_retry(
        "What is the capital of France?",
        api_key="sk-ant-your-key-here",
    )
    print(response)
```

---

## Example 5: Real-Time Streaming via WebSocket

**Problem:** You want real-time streaming responses for a chat interface without HTTP polling overhead.

**Solution:** Connect to the `/ws` WebSocket endpoint (runs on PROXY_PORT+1 by default).

```python
import asyncio
import gzip
import json
import websockets


async def stream_chat(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    ws_url: str = "ws://localhost:8767/ws",
    api_key: str = None,
):
    """Stream a chat response via WebSocket with gzip compression."""
    async with websockets.connect(ws_url) as ws:
        # Send request
        await ws.send(json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "stream": True,
            "api_key": api_key or "sk-ant-...",
        }))

        full_text = ""
        print("Assistant: ", end="", flush=True)

        async for message in ws:
            # Messages are gzip-compressed binary frames
            if isinstance(message, bytes):
                decompressed = gzip.decompress(message).decode("utf-8")
                event = json.loads(decompressed)
            else:
                event = json.loads(message)

            event_type = event.get("type")

            if event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    print(text, end="", flush=True)
                    full_text += text

            elif event_type == "message_stop":
                print()  # newline after streaming
                break

            elif event_type == "stats":
                usage = event.get("usage", {})
                print(f"\n[tokens: in={usage.get('input_tokens',0)}, "
                      f"out={usage.get('output_tokens',0)}]")

            elif "error" in event:
                print(f"\n[error: {event['error']['message']}]")
                break

        return full_text


async def main():
    # Multiple concurrent streams
    tasks = [
        stream_chat("Tell me a joke"),
        stream_chat("What is 2+2?"),
    ]
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    asyncio.run(main())
```

### Verify WebSocket Is Running

```bash
# Check proxy health (includes WS status)
curl http://localhost:8766/health | python3 -m json.tool

# Test WebSocket with websocat (CLI tool)
# pip install websocat  (or brew install websocat)
echo '{"model":"claude-haiku-4-5","messages":[{"role":"user","content":"hi"}],"max_tokens":50,"api_key":"sk-ant-..."}' \
  | websocat ws://localhost:8767/ws
```

---

## Quick Reference

| Task | Command / Code |
|------|---------------|
| Start proxy | `tokenpak serve` |
| Check health | `curl http://localhost:8766/health` |
| View stats | `curl http://localhost:8766/stats` |
| See last request | `curl http://localhost:8766/stats/last` |
| Rebuild vault index | `tokenpak vault reindex` |
| WebSocket port | `TOKENPAK_WS_PORT=8767 tokenpak serve` (default: PROXY_PORT+1) |

## Environment Variables

```bash
TOKENPAK_PORT=8766              # HTTP proxy port (default: 8766)
TOKENPAK_WS_PORT=8767           # WebSocket port (default: PROXY_PORT+1)
TOKENPAK_REQUEST_TIMEOUT=30     # Per-request upstream timeout (seconds, 0=disabled)
VAULT_INDEX_PATH=~/.tokenpak    # Path to vault index directory
TOKENPAK_INJECT_BUDGET=2200     # Max tokens injected per request
TOKENPAK_INJECT_MIN_SCORE=0.6   # Minimum similarity score for vault injection
```

## See Also

- [API Reference](api-reference.md) — Full endpoint documentation
- Compression Benchmark — Compression analysis and optimization guide
