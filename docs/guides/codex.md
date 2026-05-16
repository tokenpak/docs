---
title: "Use TokenPak with Codex CLI"
rung: 2
audience: Developers who have Codex CLI installed and want to route its ChatGPT-subscription traffic through TokenPak for cost tracking and compression.
updated: 2026-05-04
status: current
---

# Use TokenPak with Codex CLI

This guide is for developers using OpenAI Codex CLI who want to route its traffic through TokenPak for cost tracking, cache analytics, and prompt compression.

Codex CLI signs in to your ChatGPT account and stores an OAuth token at `~/.codex/auth.json`. TokenPak's Codex adapter detects the JWT-shaped bearer token, routes the request to the ChatGPT backend (`chatgpt.com/backend-api`), and applies the same compression pipeline available to OpenAI SDK callers. No code changes — only a base URL swap.

**What you need before starting:**

- Codex CLI installed and authenticated (`codex --version` works and `~/.codex/auth.json` exists)
- Python 3.10+
- No existing `OPENAI_BASE_URL` override that conflicts

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
export OPENAI_BASE_URL=http://localhost:8766/v1
codex exec "your prompt"
```

The third line points Codex CLI at TokenPak only for the current shell. Export it from `~/.bashrc` or `~/.zshrc` if you want every future Codex session routed through TokenPak.

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

Confirm the proxy is healthy:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response shape:

```json
{
  "status": "ok",
  "uptime_seconds": 3,
  "version": "1.5.0",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` for details before continuing.

---

## 2. Point Codex CLI at the proxy

Codex CLI uses the same `OPENAI_BASE_URL` environment variable as the OpenAI SDK to redirect API traffic.

```bash
export OPENAI_BASE_URL=http://localhost:8766/v1
codex exec "summarize the last commit"
```

Set the variable **in the same shell** you launch Codex from, or add it to your shell profile so it persists across sessions:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_BASE_URL=http://localhost:8766/v1
```

Then reload:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

You do not edit `~/.codex/auth.json` — Codex CLI owns that file and rotates the OAuth token itself. TokenPak reads the token from the request's `Authorization` header at proxy time, recognizes the JWT shape, and forwards byte-preserved to the ChatGPT backend.

---

## 3. Verify the proxy is intercepting traffic

Run any Codex command. Then in a second terminal:

```bash
tokenpak status
```

You should see at least one row of recent activity attributed to the `openai-codex-responses` adapter. If the table is still empty after sending a request, the env var is not in scope — see [Troubleshooting](#troubleshooting) below.

---

## 4. Check your savings

After a few requests:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Codex CLI conversations carry repeated context (file snippets, prior turns), so the compression payoff is largest on long sessions. Short one-shot prompts compress less — this is expected.

---

## Troubleshooting

### `tokenpak status` shows no activity after a Codex run

**Confirm the env var is set in the same shell that ran `codex`:**

```bash
echo "$OPENAI_BASE_URL"   # should print http://localhost:8766/v1
```

If it prints nothing, set it before invoking `codex`:

```bash
export OPENAI_BASE_URL=http://localhost:8766/v1
codex exec "your prompt"
```

Codex picks up the variable on launch. Already-running shells that started before the export will not see it — open a fresh shell or re-source your profile.

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

TokenPak forwards the OAuth bearer token from each request unchanged. If you see a 401:

1. Confirm Codex CLI is authenticated: `cat ~/.codex/auth.json` should show a `tokens.access_token` field. If the file is missing, run `codex login` first.
2. Codex tokens expire on a rolling schedule — Codex CLI refreshes them automatically when you run a command. If 401s persist, run `codex login` again to force a fresh sign-in.
3. The token TokenPak sees must be a JWT (starts with `eyJ`). If your shell exports a stale `OPENAI_API_KEY=sk-...`, Codex will send that instead and the proxy will route to `api.openai.com` rather than the ChatGPT backend. Either `unset OPENAI_API_KEY` or rely on Codex's own credential file.

### Codex requests get 403 (Cloudflare block)

The Codex adapter routes to `chatgpt.com/backend-api`, which Cloudflare protects. TokenPak uses [`curl_cffi`](https://pypi.org/project/curl-cffi/) to present a browser-shaped TLS fingerprint and bypass the block. If `curl_cffi` is not installed, the proxy falls back to `urllib3` and Cloudflare may return 403.

Install or upgrade `curl_cffi`:

```bash
pip install --upgrade curl_cffi
```

Restart the proxy after installing.

### `CODEX_HOME` set to a non-default location

If you set `CODEX_HOME` to point Codex's config elsewhere, TokenPak's credential discovery honors it as well. No proxy-side change is required — just keep the env var consistent across the shell that runs both `codex` and `tokenpak`.

---

## Removing TokenPak

To stop routing Codex CLI traffic through TokenPak:

```bash
unset OPENAI_BASE_URL
```

Remove the export from your shell profile if you added it there. Codex will return to the default ChatGPT backend on the next run. Your `~/.codex/auth.json` is untouched at every step — TokenPak never writes to it.
