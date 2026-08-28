---
title: "Use TokenPak with Claude Code"
rung: 2
audience: Developers who have Claude Code installed and want to route it through TokenPak for cost tracking and compression.
updated: 2026-05-04
status: current
---

# Use TokenPak with Claude Code

This guide is for developers who have Claude Code installed and want to route it through TokenPak for cost tracking, cache analytics, and prompt compression.

**What you need before starting:**

- Claude Code installed and authenticated (`claude --version` works)
- Python 3.10+
- No existing `ANTHROPIC_BASE_URL` set in your environment

Claude Code's existing authenticated session is sufficient for this path; a
separate Anthropic API key is not required by TokenPak.

---

## Copy-paste setup

```bash
pip install tokenpak
tokenpak setup
ANTHROPIC_BASE_URL=http://localhost:8766 claude
```

The third line sets the proxy URL only for that Claude Code launch. Use the persistent export in step 2 if you want every future Claude Code session routed through TokenPak.

---

## 1. Install and start TokenPak

```bash
pip install tokenpak
tokenpak setup
```

`tokenpak setup` detects optional provider API keys, creates `~/.tokenpak/config.yaml`, and starts the proxy on port 8766. You should see:

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
  "version": "1.21.0",
  "requests_total": 0,
  "requests_errors": 0,
  "compression_ratio_avg": 0.0
}
```

If `status` is not `"ok"`, run `tokenpak status` for details before continuing.

---

## 2. Point Claude Code at the proxy

Claude Code uses the `ANTHROPIC_BASE_URL` environment variable to redirect its Anthropic API traffic.

```bash
export ANTHROPIC_BASE_URL=http://localhost:8766
claude
```

Set the variable **in the same shell** you use to launch Claude Code, or add it to your shell profile so it persists across sessions:

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_BASE_URL=http://localhost:8766
```

Then reload:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

---

## 3. Verify the proxy is intercepting traffic

In Claude Code, run any prompt. Then in a second terminal:

```bash
tokenpak status
```

You should see at least one request in the recent activity table. If `requests_total` is still 0 after sending a prompt, the env var is not being picked up — see [Troubleshooting](#troubleshooting) below.

---

## 4. Check your savings

After a few prompts:

```bash
tokenpak cost --week      # spend by model
tokenpak savings          # tokens compressed vs. uncompressed
```

Agent-style workloads (lots of repeated context across turns) see the largest savings. A fresh session with short prompts will show minimal compression — this is expected.

---

## Troubleshooting

### Claude Code is not hitting the proxy (requests_total stays 0)

**Check that the env var is set in the correct shell:**

```bash
echo $ANTHROPIC_BASE_URL
```

It must print `http://localhost:8766`. If it prints nothing, the variable is not exported in this shell. Add the export to your shell profile and restart the terminal.

**Check that Claude Code is not using a hardcoded URL:**

Claude Code respects `ANTHROPIC_BASE_URL` when it is set. If you have a `.env` file or a `CLAUDE_API_BASE` override in your environment, it may take precedence. Unset competing variables:

```bash
unset CLAUDE_API_BASE
export ANTHROPIC_BASE_URL=http://localhost:8766
```

**Verify the proxy is still running:**

```bash
curl -s http://localhost:8766/health
```

If this returns `Connection refused`, the proxy has stopped. Restart with `tokenpak serve` (or re-run `tokenpak setup`).

### Claude Code returns auth errors after setting the proxy URL

Claude Code uses OAuth (subscription auth), not an API key. TokenPak passes the `Authorization` header through byte-for-byte to Anthropic — it does not strip or replace it. Auth errors after adding the proxy URL usually mean:

1. **Port collision** — another process is on 8766. Check with `lsof -i :8766` and kill the conflicting process, then restart TokenPak.
2. **Proxy not started** — `curl http://localhost:8766/health` returns nothing. Run `tokenpak serve`.
3. **Old env var cached** — Claude Code reads the env at startup. If you changed `ANTHROPIC_BASE_URL` after Claude Code launched, restart Claude Code.

### The env var is set but Claude Code ignores it after a system update

Some package managers (Homebrew, conda) reset PATH and environment on upgrade. After a Claude Code or shell update, re-check `echo $ANTHROPIC_BASE_URL` in a fresh terminal and re-add the export to your shell profile if it disappeared.

### tokenpak savings shows 0 after several prompts

Compression applies to prompts above a configurable default threshold. Short prompts are passed through unchanged. To confirm compression is running for longer prompts, use `tokenpak status` — the `compression_ratio_avg` field in `/health` shows the running average.

---

## Removing TokenPak

To stop routing Claude Code through TokenPak:

```bash
unset ANTHROPIC_BASE_URL
```

Remove the export from your shell profile if you added it there. Claude Code will return to its default Anthropic endpoint immediately on next launch.
