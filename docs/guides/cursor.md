---
title: "Use TokenPak with Cursor"
rung: 2
audience: Developers using Cursor who want to try routing model requests through TokenPak for request records and cost tracking.
updated: 2026-09-29
status: compatibility-target
---

# Use TokenPak with Cursor

> **Compatibility target, not yet independently verified.** The first-class integrations are Claude Code and Codex; this guide describes an expected setup for Cursor.

This guide is for developers using Cursor who want to route chat, composer, or agent model requests through TokenPak for request records, cost tracking, and cache analytics.

Cursor provider settings change over time. Use the stable rule: configure Cursor to use an OpenAI-compatible custom base URL, then point that URL at TokenPak's local `/v1` endpoint.

**What you need before starting:**

- Cursor installed
- Python 3.10+
- A valid upstream API key for the OpenAI-compatible provider/model you choose
- No existing Cursor custom base URL pointing somewhere else

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
curl -s http://localhost:8766/health | python3 -m json.tool
```

Then configure Cursor with this base URL:

```text
OpenAI-compatible base URL: http://localhost:8766/v1
```

Use the same provider API key you would normally use in Cursor. TokenPak forwards that key upstream; it does not replace it.

---

## 1. Install and start TokenPak

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
  "version": "1.25.1",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` before changing Cursor settings.

---

## 2. Point Cursor at the proxy

Open Cursor's AI/model settings. The exact labels vary by Cursor release, but the setup is usually under settings for models, API keys, or OpenAI-compatible providers.

1. Choose the OpenAI or OpenAI-compatible provider path.
2. Enter the upstream API key you normally use for that provider.
3. Set the custom or override base URL to:

   ```text
   http://localhost:8766/v1
   ```

4. Choose the model ID you normally use.
5. Save settings and restart the active chat/composer/agent session.

If Cursor exposes both a provider URL and a separate API endpoint URL, set the API/base URL field only. Do not change model names unless you intentionally want to use a different model.

---

## 3. Optional: launch Cursor with env vars

Most users should configure Cursor in the UI. If your Cursor build or remote environment reads OpenAI-compatible environment variables, launch Cursor from a shell that has:

```bash
export OPENAI_BASE_URL=http://localhost:8766/v1
export OPENAI_API_KEY="$OPENAI_API_KEY"
cursor .
```

GUI apps may not inherit shell environment variables on every OS. If the UI setting exists, prefer the UI setting because it is visible and easier to verify.

---

## 4. Verify Cursor traffic is routed through TokenPak

Ask Cursor a tiny prompt, such as:

```text
Reply with one sentence confirming this request reached the configured model.
```

Then check TokenPak:

```bash
tokenpak status
```

You should see at least one recent request. If `requests_total` is still 0 after Cursor responds, Cursor is not using the TokenPak base URL — see [Troubleshooting](#troubleshooting).

---

## 5. Check your usage and savings

After a few Cursor turns:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # recorded token savings; zero is a valid result
```

The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved. Explicit context tools can reduce eligible content; measure their effect with `tokenpak savings`.

---

## Troubleshooting

### requests_total stays 0 after Cursor responds

Cursor is not using the TokenPak base URL. Re-open Cursor's model/provider settings and confirm:

- The provider path supports an OpenAI-compatible custom base URL.
- The base URL is exactly `http://localhost:8766/v1`.
- You saved the setting and restarted the active chat/composer/agent session.
- Workspace-level Cursor settings are not overriding your user-level settings.

### Port collision — proxy fails to start on 8766

If 8766 is already in use:

```bash
lsof -i :8766
```

Stop the conflicting process, then restart TokenPak. Alternatively, run TokenPak on another port and update Cursor's base URL:

```bash
TOKENPAK_PORT=8767 tokenpak serve
```

Then set Cursor's base URL to:

```text
http://localhost:8767/v1
```

### Proxy not started — Cursor shows connection errors

Verify the proxy directly:

```bash
curl -s http://localhost:8766/health
```

If this returns `Connection refused`, start the proxy:

```bash
tokenpak serve
```

You can also re-run `tokenpak setup` if this is your first install.

### Auth errors — 401 from the proxy

TokenPak forwards the key you entered in Cursor. If you see a 401:

1. Confirm the key in Cursor matches the provider/model you selected.
2. Confirm the key has not expired or been revoked in the provider dashboard.
3. Confirm Cursor is using an OpenAI-compatible provider path with `/v1` at the end of the base URL.

### Env-var or editor caching — settings do not take effect

Cursor may keep a running chat/composer/agent session alive with old provider settings. After changing the base URL:

1. Stop the current agent/chat session.
2. Reload the Cursor window if the value still appears stale.
3. Start a new Cursor session.
4. Check `tokenpak status` again.

In remote Cursor sessions, `localhost` means the machine where the Cursor extension host or model client runs. Run TokenPak on that same host, or use a reachable proxy URL.

### savings shows 0 after several turns

Zero is a correct result for a forwarded request: the default proxy preserves conversation turns. Use `tokenpak status` to confirm requests reach the proxy, and check `compression_ratio_avg` in the `/health` response.

---

## Removing TokenPak

To stop routing Cursor through TokenPak, clear the custom base URL field or reset it to the provider default. Restart the active Cursor session so the change takes effect.
