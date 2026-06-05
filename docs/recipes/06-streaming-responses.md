# Recipe: Streaming Responses

> **Status: Verified runnable.** TokenPak's proxy is a byte-preserving passthrough, so streaming works transparently: when your client requests a streaming response, the proxy forwards the upstream provider's stream (server-sent events) back to your client verbatim. The commands below run against the default proxy at `http://127.0.0.1:8766`.
>
> Note: there is **no** dedicated `streaming:` config block, no separate `-streaming` model names, and no proxy-side token buffering in the current release — streaming is enabled by the `"stream": true` flag in the request body and the provider's own SSE response, which the proxy passes through unchanged.

**What this solves:** Receiving responses token-by-token instead of waiting for the full response, improving perceived latency.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- A streaming-aware client (`curl --no-buffer`, Python `requests` with `stream=True`, Node.js streams)
- A valid API key for your provider

## Start the proxy

```bash
tokenpak serve   # listens on http://127.0.0.1:8766
```

No special config is required for streaming — the proxy forwards the upstream stream as-is.

## Test & Verify

**Streaming with curl (server-sent events):**
```bash
curl -N -X POST http://127.0.0.1:8766/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 128,
    "stream": true,
    "messages": [{"role": "user", "content": "Write a haiku about API proxies"}]
  }'

# Output (illustrative shape — exact events come from the upstream provider):
# event: content_block_delta
# data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"API"}}
# event: content_block_delta
# data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" proxies"}}
# ...
```

`curl -N` (`--no-buffer`) disables curl's output buffering so you see events as they arrive.

**Streaming with Python:**
```python
import os
import requests

with requests.post(
    "http://127.0.0.1:8766/v1/messages",
    headers={
        "Content-Type": "application/json",
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
    },
    json={
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 128,
        "stream": True,
        "messages": [{"role": "user", "content": "Write a 2-sentence story"}],
    },
    stream=True,
) as response:
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))
```

**Streaming with Node.js:**
```javascript
async function streamResponse() {
  const response = await fetch('http://127.0.0.1:8766/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 128,
      stream: true,
      messages: [{ role: 'user', content: 'Count to 5' }],
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    process.stdout.write(decoder.decode(value));
  }
}

streamResponse();
```

## What Just Happened

1. **Client sends** a request with `"stream": true`.
2. **The proxy forwards** the request to the upstream provider with streaming enabled.
3. **As the provider emits SSE events**, the proxy passes them through to your client verbatim (byte-preserving passthrough).
4. **Your client renders** the deltas as they arrive.

Because the proxy does not buffer or rewrite the stream, the streaming behavior your client sees is the provider's own — TokenPak adds transport pass-through, not a separate streaming engine.

## Common Pitfalls

**Client doesn't handle the SSE format**
- ❌ Wrong: `JSON.parse()` the whole streamed body (it is a sequence of `data:` lines, not one JSON document).
- ✅ Right: Parse SSE line-by-line; each `data:` line carries a JSON payload.

**Output buffering hides the stream**
- ❌ Wrong: Plain `curl` (buffers output) makes the response look non-streaming.
- ✅ Right: Use `curl -N` / `--no-buffer`, or a client that reads incrementally.

**Not handling connection drops**
- ❌ Wrong: Assume the streaming connection never breaks.
- ✅ Right: Implement reconnect/retry logic for long streams.

**Measuring total time instead of time-to-first-token**
- ❌ Wrong: Report total response time as "latency."
- ✅ Right: Track time-to-first-token separately — that's where streaming helps perceived latency.
