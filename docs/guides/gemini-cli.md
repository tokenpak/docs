---
title: "Use TokenPak with Gemini CLI"
rung: 2
audience: Developers using Google's Gemini CLI who want to route Gemini requests through TokenPak.
updated: 2026-05-04
status: current
---

# Use TokenPak with Gemini CLI

This guide is for developers using Google's Gemini CLI who want TokenPak cost tracking, telemetry, and compression on Gemini requests.

Gemini CLI supports a custom Gemini API base URL through `GOOGLE_GEMINI_BASE_URL`. Point that variable at TokenPak's local proxy. TokenPak then forwards Google Generative AI requests upstream while recording usage.

**What you need before starting:**

- Gemini CLI (`@google/gemini-cli`) installed
- TokenPak installed locally
- `GEMINI_API_KEY` for Google AI Studio
- A shell where you can export environment variables before launching `gemini`

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
curl -s http://localhost:8766/health | python3 -m json.tool
```

Then launch Gemini CLI from the same shell:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_GEMINI_BASE_URL="http://localhost:8766"
gemini -p "Reply with one sentence confirming Gemini CLI is routed through TokenPak."
```

Do not add `/v1` to `GOOGLE_GEMINI_BASE_URL`. Gemini CLI sends Google Generative AI paths such as `/v1beta/models/...:generateContent`; TokenPak detects those paths and routes them to the Google adapter.

---

## 1. Start TokenPak

```bash
pip install tokenpak
tokenpak setup
```

`tokenpak setup` detects provider keys, creates `~/.tokenpak/config.yaml`, and starts the proxy on port 8766. You should see:

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
  "version": "1.21.0",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` before launching Gemini CLI.

---

## 2. Launch Gemini CLI through TokenPak

Export the Gemini key and base URL in the same terminal where you run `gemini`:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_GEMINI_BASE_URL="http://localhost:8766"
gemini -p "Say hello through TokenPak."
```

Use `GOOGLE_GEMINI_BASE_URL` for Google AI Studio / Gemini API traffic. If you intentionally use Vertex AI mode, Gemini CLI also supports `GOOGLE_VERTEX_BASE_URL`, but Vertex setup has separate project and location requirements; this guide focuses on the Google AI Studio path.

---

## 3. Verify traffic is routed through TokenPak

After Gemini CLI returns a response:

```bash
tokenpak status
```

You should see at least one recent request. You can also check `/health` again:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

If `requests_total` remains 0, Gemini CLI did not inherit `GOOGLE_GEMINI_BASE_URL`; see [Troubleshooting](#troubleshooting).

---

## 4. Check your savings

After a few Gemini CLI prompts:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Short prompts may pass through with little or no compression. Larger repeated context is where TokenPak has the most room to reduce tokens.

---

## Troubleshooting

### requests_total stays 0 after Gemini CLI responds

Gemini CLI is not using the TokenPak base URL. Confirm:

- `GOOGLE_GEMINI_BASE_URL` is exported in the same shell that runs `gemini`.
- The value is exactly `http://localhost:8766`.
- You did not include `/v1` or `/v1beta` in the base URL.
- You restarted Gemini CLI after changing the variable.

Run this in the same shell before launching Gemini CLI:

```bash
printf '%s\n' "$GOOGLE_GEMINI_BASE_URL"
```

### Proxy not started — Gemini CLI shows connection errors

Verify the proxy directly:

```bash
curl -s http://localhost:8766/health
```

If this returns `Connection refused`, start the proxy:

```bash
tokenpak serve
```

You can also re-run `tokenpak setup` if this is your first install.

### Port collision — proxy fails to start on 8766

If 8766 is already in use:

```bash
lsof -i :8766
```

Stop the conflicting process, then restart TokenPak. Alternatively, run TokenPak on another port and update Gemini CLI's base URL:

```bash
TOKENPAK_PORT=8767 tokenpak serve
export GOOGLE_GEMINI_BASE_URL="http://localhost:8767"
```

### Auth errors — 401 or invalid API key

Gemini CLI still needs a valid Gemini API key. TokenPak does not replace credentials. Confirm:

1. `GEMINI_API_KEY` is exported in the same shell that runs `gemini`.
2. The key is valid for Google AI Studio / Gemini API.
3. You are not mixing Vertex AI variables with Google AI Studio variables.

### Environment caching — variable changes do not take effect

Gemini CLI reads environment variables when the process starts. After changing `GOOGLE_GEMINI_BASE_URL`:

1. Stop the current `gemini` process.
2. Export the new value.
3. Start a new `gemini` command.
4. Check `tokenpak status` again.

If you run Gemini CLI from an editor task runner or terminal multiplexer, make sure that runner inherits the updated environment.

### Tools or function-calling requests fail

TokenPak's Google adapter does not yet translate Google function-calling/tool schemas. Plain text prompts are supported; tool-heavy workflows may fail loudly instead of being silently altered. Use Claude Code, OpenAI SDK, or Cline routes for tool-calling workflows until Google tool translation ships.

---

## See also

- [Google adapter](../adapters/google.md)
- [LiteLLM adapter](../adapters/litellm.md)
- [Troubleshooting](../troubleshooting.md)
