---
title: "Use TokenPak with the Anthropic Python SDK"
rung: 2
audience: Developers using the Anthropic Python SDK who want to route API calls through TokenPak for cost tracking and compression.
updated: 2026-05-04
status: current
---

# Use TokenPak with the Anthropic Python SDK

This guide is for developers using the Anthropic Python SDK who want to route API calls through TokenPak for cost tracking, cache analytics, and prompt compression.

TokenPak accepts Anthropic Messages API traffic at the same local proxy URL Claude Code uses. You can point the SDK at TokenPak with `ANTHROPIC_BASE_URL` or with the `base_url` argument in code.

**What you need before starting:**

- Python 3.10+
- Anthropic Python SDK installed (`pip show anthropic` works)
- A valid `ANTHROPIC_API_KEY`
- No existing `ANTHROPIC_BASE_URL` override that points somewhere else

---

## Copy-paste setup

```bash
pip install tokenpak anthropic
tokenpak setup
export ANTHROPIC_BASE_URL=http://localhost:8766
```

Then run your existing Anthropic SDK script normally in the same shell.

---

## 1. Install and start TokenPak

```bash
pip install tokenpak
tokenpak setup
```

`tokenpak setup` detects optional provider API keys, creates `~/.tokenpak/config.yaml`, and starts the proxy on port 8766. You should see:

```text
TokenPak proxy listening on http://localhost:8766
```

Confirm the proxy is healthy:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response shape:

```json
{
  "status": "ok",
  "uptime_seconds": 3,
  "version": "1.23.0",
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
export ANTHROPIC_BASE_URL=http://localhost:8766
```

The Anthropic SDK reads `ANTHROPIC_BASE_URL` when you create the client. Your code can stay small:

```python
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY from env
message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=64,
    messages=[{"role": "user", "content": "Say hello from TokenPak."}],
)
print(message.content[0].text)
```

**Option B — explicit `base_url` in code:**

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8766",
    api_key="YOUR_ANTHROPIC_API_KEY",  # or leave to env: ANTHROPIC_API_KEY
)
```

Both options route SDK requests through TokenPak. Use the env-var approach when you do not want proxy settings committed to source control.

---

## 3. Verify the proxy is intercepting traffic

Run the code snippet above. Then in a second terminal:

```bash
tokenpak status
```

You should see at least one request in the recent activity table. If `requests_total` is still 0 after sending a request, the SDK is not using the proxy URL — see [Troubleshooting](#troubleshooting).

---

## 4. Check your savings

After a few requests:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Agent-style workloads with large repeated context see the largest savings. Short one-off messages may show little or no compression because they fall below the default compression threshold.

---

## Troubleshooting

### requests_total stays 0 after sending a request

**Confirm the env var is visible to Python:**

```python
import os
print(os.environ.get("ANTHROPIC_BASE_URL"))  # should print http://localhost:8766
```

If it prints `None`, set the variable before starting Python:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8766
python your_script.py
```

If your script creates `Anthropic(base_url=...)`, that explicit value overrides the env var. Update the argument to `http://localhost:8766` or remove it and rely on `ANTHROPIC_BASE_URL`.

### Port collision — proxy fails to start on 8766

If 8766 is already in use:

```bash
lsof -i :8766
```

Stop the conflicting process, then restart TokenPak. Alternatively, run TokenPak on another port and point the SDK there:

```bash
TOKENPAK_PORT=8767 tokenpak serve
export ANTHROPIC_BASE_URL=http://localhost:8767
```

### Proxy not started — connection refused

If the SDK raises a connection error after setting `ANTHROPIC_BASE_URL`:

```bash
curl -s http://localhost:8766/health
```

If this returns `Connection refused`, start the proxy:

```bash
tokenpak serve
```

You can also re-run `tokenpak setup` if this is your first install.

### Auth errors — 401 from the proxy

TokenPak forwards your Anthropic credential upstream. It does not replace a bad key with its own key. If you see a 401:

1. Confirm the key exists in the same shell: `echo $ANTHROPIC_API_KEY` should print a value.
2. Confirm the key has not expired or been revoked in the Anthropic Console.
3. Confirm you are not mixing auth modes. SDK API-key auth uses `ANTHROPIC_API_KEY`; Claude Code subscription auth is separate and is covered in the [Claude Code guide](claude-code.md).

### Env var caching — changes do not take effect

The SDK reads `ANTHROPIC_BASE_URL` when `Anthropic()` is created. If you change the env var after your app has already created the client, restart the Python process or create a new client instance:

```python
from anthropic import Anthropic

client = Anthropic(base_url="http://localhost:8766")
```

In notebooks, restart the kernel after changing shell environment variables.

### savings shows 0 after several requests

Compression runs on prompts above a configurable default threshold. Short chat messages are passed through unchanged. For larger prompts, use `tokenpak status` and check `compression_ratio_avg` in the `/health` response.

---

## Removing TokenPak

To stop routing Anthropic SDK traffic through TokenPak:

```bash
unset ANTHROPIC_BASE_URL
```

Remove the export from your shell profile if you added it there. The SDK returns to the default Anthropic endpoint the next time you create an `Anthropic()` client.
