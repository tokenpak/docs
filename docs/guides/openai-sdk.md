---
title: "Use TokenPak with the OpenAI Python SDK"
rung: 2
audience: Developers using the OpenAI Python SDK (or any OpenAI-compatible client) who want to route traffic through TokenPak for cost tracking and compression.
updated: 2026-05-04
status: current
---

# Use TokenPak with the OpenAI Python SDK

This guide is for developers using the OpenAI Python SDK (or any client that accepts a custom `base_url`) who want to route traffic through TokenPak for cost tracking, cache analytics, and prompt compression.

TokenPak's proxy speaks the OpenAI wire protocol — no code changes required, only a base URL swap.

**What you need before starting:**

- OpenAI Python SDK installed (`pip show openai` works)
- Python 3.10+
- No existing `OPENAI_BASE_URL` override that conflicts

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
export OPENAI_BASE_URL=http://localhost:8766/v1
```

Then run your existing OpenAI SDK script normally in the same shell.

---

## 1. Install and start TokenPak

```bash
pip install tokenpak
tokenpak setup
```

`tokenpak setup` detects your API keys, creates `~/.tokenpak/config.yaml`, and starts the proxy on port 8766. You should see:

```
TokenPak proxy listening on http://localhost:8766
```

Confirm the proxy is healthy:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "ok",
  "uptime_seconds": 3,
  "version": "1.13.0",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` for details before continuing.

---

## 2. Point the SDK at the proxy

**Option A — environment variable (recommended for scripts and CI):**

```bash
export OPENAI_BASE_URL=http://localhost:8766/v1
```

The SDK picks this up automatically. Your existing code does not need to change:

```python
from openai import OpenAI

client = OpenAI()  # reads OPENAI_BASE_URL and OPENAI_API_KEY from env
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

**Option B — explicit `base_url` in code:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8766/v1",
    api_key="YOUR_OPENAI_API_KEY",   # or leave to env: OPENAI_API_KEY
)
```

Both options are equivalent. Use the env-var approach for shared codebases so the proxy URL does not get committed to source control.

---

## 3. Verify the proxy is intercepting traffic

Run the code snippet above. Then in a second terminal:

```bash
tokenpak status
```

You should see at least one request in the recent activity table. If `requests_total` is still 0 after sending a request, the env var is not being picked up — see [Troubleshooting](#troubleshooting) below.

---

## 4. Check your savings

After a few requests:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Agent-style workloads (large system prompts, repeated context) see the largest savings. Short one-off completions will show minimal compression — this is expected behavior.

---

## Troubleshooting

### requests_total stays 0 after sending a request

**Confirm the env var is set in the correct Python process:**

```python
import os
print(os.environ.get("OPENAI_BASE_URL"))  # should print http://localhost:8766/v1
```

If it prints `None`, the variable is not in scope. Set it before importing `openai`:

```bash
export OPENAI_BASE_URL=http://localhost:8766/v1
python your_script.py
```

**Check the SDK version:**

`OPENAI_BASE_URL` is read by `openai>=1.0.0`. Older versions use `openai.api_base`. Check with `pip show openai`. If you're on `openai<1.0.0`, upgrade:

```bash
pip install --upgrade openai
```

### Port collision — proxy fails to start on 8766

If 8766 is already in use:

```bash
lsof -i :8766
```

Kill the conflicting process, then restart TokenPak. Alternatively, change the port:

```bash
TOKENPAK_PORT=8767 tokenpak serve
export OPENAI_BASE_URL=http://localhost:8767/v1
```

### Auth errors — 401 from the proxy

TokenPak forwards your `OPENAI_API_KEY` to OpenAI unmodified. If you see a 401:

1. Confirm `OPENAI_API_KEY` is set and valid: `echo $OPENAI_API_KEY` should print your key.
2. Confirm the key has not expired or been revoked in the OpenAI dashboard.
3. If you're routing to a different provider (Anthropic, Azure), make sure the key matches the target — TokenPak infers the provider from the request body shape.

### Responses look correct but savings are zero

Compression runs on prompts above a configurable default threshold. Short chat messages are passed through unchanged. For larger prompts, use `tokenpak status` and check `compression_ratio_avg` in the `/health` response — a value of `0.0` after many requests suggests all prompts fell below the threshold. Lower the threshold with:

```bash
export TOKENPAK_COMPACT_THRESHOLD_TOKENS=1000
```

---

## Removing TokenPak

To stop routing OpenAI SDK traffic through TokenPak:

```bash
unset OPENAI_BASE_URL
```

Remove the export from your shell profile if you added it there. The SDK will return to the default OpenAI endpoint on the next run.
