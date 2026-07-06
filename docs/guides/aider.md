---
title: "Use TokenPak with Aider"
rung: 2
audience: Developers using Aider who want to route chat/edit traffic through TokenPak with Aider's OpenAI-compatible CLI flags.
updated: 2026-05-04
status: current
---

# Use TokenPak with Aider

This guide is for developers using Aider who want to route chat/edit traffic through TokenPak for cost tracking, cache analytics, and prompt compression.

Aider can send requests to an OpenAI-compatible endpoint. Point that endpoint at TokenPak with `--openai-api-base`, then use Aider's `openai/<model-name>` model format.

**What you need before starting:**

- Aider installed (`aider --version` works)
- TokenPak installed and configured (`tokenpak setup` works)
- A provider API key available in the shell that starts Aider, such as `OPENAI_API_KEY`
- A Git repository for Aider to edit

---

## Copy-paste setup

Run this from the repository you want Aider to edit:

```bash
tokenpak setup
curl -s http://localhost:8766/health | python3 -m json.tool
aider --model openai/gpt-4o --openai-api-base http://localhost:8766/v1
```

Use a model name your upstream provider account supports. The important pieces are:

- `--openai-api-base http://localhost:8766/v1` sends Aider traffic through TokenPak.
- `--model openai/<model-name>` keeps Aider on its OpenAI-compatible provider path.

---

## 1. Start TokenPak

```bash
tokenpak setup
```

`tokenpak setup` creates or updates `~/.tokenpak/config.yaml` and starts the local proxy on port 8766. Confirm the proxy is healthy before starting Aider:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

Expected response:

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

If `status` is not `"ok"`, run `tokenpak status` and fix the reported issue before continuing.

---

## 2. Start Aider with TokenPak as the API base

From your project repository:

```bash
aider --model openai/gpt-4o --openai-api-base http://localhost:8766/v1
```

For a different OpenAI-compatible model, keep the `openai/` prefix and replace the model suffix:

```bash
aider --model openai/gpt-4.1 --openai-api-base http://localhost:8766/v1
```

Aider still reads your provider key from the environment. For OpenAI, that is usually:

```bash
export OPENAI_API_KEY="your-openai-key"
```

TokenPak forwards the provider credential without rewriting it.

---

## 3. Verify Aider traffic reaches TokenPak

Send a small request in Aider, then check TokenPak from another terminal:

```bash
tokenpak status
```

You should see at least one recent request. You can also inspect `/health` directly:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

`requests_total` should increase after an Aider request. If it stays at `0`, Aider is not using the TokenPak base URL.

---

## 4. Check savings after real coding sessions

After a few Aider turns with repository context:

```bash
tokenpak savings
tokenpak cost --week
```

Aider sessions with large file context usually show more savings than short one-message chats. Short prompts may pass through unchanged when they are below TokenPak's compression threshold.

---

## Troubleshooting

### requests_total stays 0

Confirm you started Aider with the base URL flag in the same command:

```bash
aider --model openai/gpt-4o --openai-api-base http://localhost:8766/v1
```

Then confirm TokenPak is listening:

```bash
curl -s http://localhost:8766/health | python3 -m json.tool
```

If the health check fails, restart TokenPak before starting Aider again.

### Aider says the model is unknown

Use the OpenAI-compatible model prefix:

```bash
aider --model openai/gpt-4o --openai-api-base http://localhost:8766/v1
```

The format is `openai/<model-name>`. The suffix must be a model your upstream provider accepts.

### Auth errors from the provider

TokenPak forwards your provider key. Confirm the key exists in the same shell that starts Aider:

```bash
printenv OPENAI_API_KEY
```

If the variable is empty, export it and restart Aider:

```bash
export OPENAI_API_KEY="your-openai-key"
aider --model openai/gpt-4o --openai-api-base http://localhost:8766/v1
```

### Port 8766 is already in use

Find the process using the port:

```bash
lsof -i :8766
```

Stop the conflicting process or start TokenPak on another port, then pass that port to Aider:

```bash
TOKENPAK_PORT=8767 tokenpak serve
aider --model openai/gpt-4o --openai-api-base http://localhost:8767/v1
```

### Savings show as zero

TokenPak may pass short prompts through unchanged. Aider requests with larger repository context should show compression over time. Check request counts first with `tokenpak status`, then run:

```bash
tokenpak savings
```
