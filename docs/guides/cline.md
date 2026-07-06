---
title: "Use TokenPak with Cline"
rung: 2
audience: Developers using Cline in VS Code who want to route model requests through TokenPak for cost tracking and compression.
updated: 2026-05-04
status: current
---

# Use TokenPak with Cline

This guide is for developers using Cline in VS Code who want to route model requests through TokenPak for cost tracking, cache analytics, and prompt compression.

Cline provider settings change across releases. Use the provider-agnostic rule: choose a provider mode that lets you set a custom OpenAI-compatible base URL, then point it at TokenPak's local `/v1` endpoint. If your Cline build exposes an Anthropic-compatible custom base URL instead, use the Anthropic URL noted below.

**What you need before starting:**

- VS Code with the Cline extension installed
- Python 3.10+
- A valid upstream API key for the provider/model you choose in Cline
- No existing custom base URL in Cline pointing somewhere else

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
curl -s http://localhost:8766/health | python3 -m json.tool
```

Then configure Cline with one of these base URLs:

```text
OpenAI-compatible base URL: http://localhost:8766/v1
Anthropic-compatible base URL: http://localhost:8766
```

Use the OpenAI-compatible URL when Cline asks for an OpenAI-compatible provider. Use the Anthropic-compatible URL only if your Cline version explicitly exposes a custom Anthropic base URL field.

---

## 1. Install and start TokenPak

```bash
pip install tokenpak
tokenpak setup
```

`tokenpak setup` detects your API keys, creates `~/.tokenpak/config.yaml`, and starts the proxy on port 8766. You should see:

```text
TokenPak proxy listening on http://localhost:8766
```

Confirm the proxy is healthy before changing Cline settings:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response shape:

```json
{
  "status": "ok",
  "uptime_seconds": 3,
  "version": "1.11.0",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` for details before continuing.

---

## 2. Point Cline at the proxy

Open Cline's model/provider settings in VS Code. The exact labels vary by Cline version, but the safe path is:

1. Choose the provider mode whose label is closest to **OpenAI Compatible**, **OpenAI-compatible**, or **custom OpenAI-compatible provider**.
2. Set the base URL to:

   ```text
   http://localhost:8766/v1
   ```

3. Enter the upstream API key you normally use for that provider. TokenPak forwards it to the provider; it does not replace it.
4. Choose the model ID you normally use with that provider.
5. Save the settings and restart the Cline task if one is already running.

If your Cline version exposes a custom Anthropic-compatible base URL, use this URL instead:

```text
http://localhost:8766
```

Do not add `/v1` to Anthropic-compatible settings. Anthropic SDK-style clients add the versioned path themselves.

---

## 3. Verify Cline traffic is routed through TokenPak

Ask Cline to run a small prompt, such as:

```text
Reply with one sentence confirming this request reached the configured model.
```

Then in a terminal:

```bash
tokenpak status
```

You should see at least one request in the recent activity table. If `requests_total` is still 0 after Cline sends a prompt, Cline is not using the TokenPak base URL — see [Troubleshooting](#troubleshooting).

---

## 4. Check your savings

After a few Cline turns:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Cline agent tasks can include repeated repository context, tool results, and instructions. Those larger repeated payloads are where TokenPak has the most room to reduce tokens. Very short prompts may show little or no compression.

---

## Troubleshooting

### requests_total stays 0 after Cline sends a prompt

Cline is not using the TokenPak base URL. Re-open Cline's provider settings and confirm:

- Provider mode is OpenAI-compatible or another custom-base-url mode.
- Base URL is exactly `http://localhost:8766/v1` for OpenAI-compatible settings.
- Base URL is exactly `http://localhost:8766` for Anthropic-compatible settings.
- The running Cline task was restarted after you changed settings.

Some Cline versions keep provider settings per workspace. Check both user-level and workspace-level settings if the value keeps reverting.

### Port collision — proxy fails to start on 8766

If 8766 is already in use:

```bash
lsof -i :8766
```

Stop the conflicting process, then restart TokenPak. Alternatively, run TokenPak on another port and update Cline's base URL:

```bash
TOKENPAK_PORT=8767 tokenpak serve
```

Then use:

```text
OpenAI-compatible base URL: http://localhost:8767/v1
Anthropic-compatible base URL: http://localhost:8767
```

### Proxy not started — Cline shows connection errors

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

TokenPak forwards the key you entered in Cline. It does not silently substitute a different key. If you see a 401:

1. Confirm the key in Cline matches the provider/model you selected.
2. Confirm the key has not expired or been revoked in the provider dashboard.
3. Confirm the base URL shape matches the provider mode. OpenAI-compatible uses `/v1`; Anthropic-compatible does not.

### Editor or env caching — settings do not take effect

Cline can keep a running task alive with old provider settings. After changing the base URL:

1. Stop the current Cline task.
2. Reload the VS Code window if the value still appears stale.
3. Start a new Cline task.
4. Check `tokenpak status` again.

In remote VS Code sessions, `localhost` means the machine where the Cline extension host runs. If VS Code is connected to a remote host, run TokenPak on that remote host or use a reachable proxy URL.

### savings shows 0 after several turns

Compression runs on prompts above a configurable default threshold. Short Cline tasks are passed through unchanged. For larger tasks, use `tokenpak status` and check `compression_ratio_avg` in the `/health` response.

---

## Removing TokenPak

To stop routing Cline through TokenPak, switch Cline's provider settings back to the provider's default base URL or clear the custom base URL field. Restart the Cline task so the new setting takes effect.
