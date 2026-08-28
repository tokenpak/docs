---
title: "Use TokenPak with Continue.dev"
rung: 2
audience: Developers using Continue.dev who want to route chat and autocomplete requests through TokenPak with a local JSON provider config.
updated: 2026-05-04
status: current
---

# Use TokenPak with Continue.dev

This guide is for developers using Continue.dev who want to route chat and autocomplete requests through TokenPak for cost tracking, TokenPak cache analytics, and prompt compression.

Continue reads model providers from `~/.continue/config.json`. Add a TokenPak-backed OpenAI-compatible model entry that points `apiBase` at `http://localhost:8766/v1`.

**What you need before starting:**

- Continue installed in VS Code or JetBrains
- TokenPak installed and configured (`tokenpak setup` works)
- A provider API key available to Continue, such as `OPENAI_API_KEY`
- An existing `~/.continue/config.json` file, or permission to create one

---

## Copy-paste setup

Start TokenPak, then add this model entry to `~/.continue/config.json`:

```bash
tokenpak setup
curl -s http://localhost:8766/health | python3 -m json.tool
```

```json
{
  "models": [
    {
      "title": "GPT-4o via TokenPak",
      "provider": "openai",
      "model": "gpt-4o",
      "apiKey": "YOUR_OPENAI_API_KEY",
      "apiBase": "http://localhost:8766/v1"
    }
  ]
}
```

If your config already has `models`, add the TokenPak object to the existing array instead of replacing your current providers.

---

## 1. Start TokenPak

```bash
tokenpak setup
```

Confirm the local proxy is healthy:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response:

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

If `status` is not `"ok"`, run `tokenpak status` and fix the reported issue before changing Continue.

---

## 2. Add a TokenPak model to Continue

Open `~/.continue/config.json`. If it already contains models, preserve them and add a new object to the `models` array:

```json
{
  "models": [
    {
      "title": "GPT-4o via TokenPak",
      "provider": "openai",
      "model": "gpt-4o",
      "apiKey": "YOUR_OPENAI_API_KEY",
      "apiBase": "http://localhost:8766/v1"
    }
  ]
}
```

For autocomplete, add or update `tabAutocompleteModel` with the same TokenPak base URL:

```json
{
  "tabAutocompleteModel": {
    "title": "GPT-4o Mini via TokenPak",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "apiKey": "YOUR_OPENAI_API_KEY",
    "apiBase": "http://localhost:8766/v1"
  }
}
```

Use a model name your upstream provider account supports. TokenPak forwards the provider credential without rewriting it.

---

## 3. Restart Continue and select the TokenPak model

1. Save `~/.continue/config.json`.
2. Reload your editor window.
3. Open Continue.
4. Select **GPT-4o via TokenPak** from the model picker.
5. Send a short chat request.

Continue should respond normally. If the request fails, check the troubleshooting section below before changing provider settings again.

---

## 4. Verify Continue traffic reaches TokenPak

After sending a Continue request, check TokenPak from a terminal:

```bash
tokenpak status
```

You should see at least one recent request. You can also inspect `/health` directly:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

`requests_total` should increase after a Continue request. If it stays at `0`, Continue is not using the TokenPak `apiBase` value.

---

## 5. Check savings after real coding sessions

After several Continue turns with file or workspace context:

```bash
tokenpak savings
tokenpak cost --week
```

Continue requests with larger context usually show more savings than short one-line chats. Short prompts may pass through unchanged when they are below TokenPak's compression threshold.

---

## Troubleshooting

### requests_total stays 0

Confirm the selected Continue model is the TokenPak-backed entry and that its config has the local base URL:

```json
{
  "apiBase": "http://localhost:8766/v1"
}
```

Then confirm TokenPak is listening:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Reload the editor after changing `~/.continue/config.json`; Continue may not pick up file edits until the extension restarts.

### Continue reports an invalid JSON config

Validate the file before restarting the editor:

```bash
python3 -m json.tool ~/.continue/config.json >/tmp/continue-config-check.json
```

If this command fails, fix the comma or brace named in the error output. JSON does not allow comments or trailing commas.

### Auth errors from the provider

TokenPak forwards your provider key. If you use a placeholder in `apiKey`, replace it with a real key or configure Continue to read the key from your environment according to your Continue setup.

For OpenAI-compatible routing, the key must match the upstream provider used by the selected model.

### Port 8766 is already in use

Find the process using the port:

```bash
lsof -i :8766
```

Stop the conflicting process or start TokenPak on another port, then update Continue's `apiBase` to match:

```bash
TOKENPAK_PORT=8767 tokenpak serve
```

```json
{
  "apiBase": "http://localhost:8767/v1"
}
```

### Existing Continue providers disappeared

Restore your previous `models` entries and add the TokenPak entry alongside them. Do not replace the full `models` array unless you mean to remove the existing providers.
