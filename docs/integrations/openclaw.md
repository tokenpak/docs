---
title: "OpenClaw integration"
created: 2026-04-24
---

# OpenClaw integration

Run [OpenClaw](https://openclaw.com)'s agents through TokenPak's compression
+ caching pipeline, with full Claude Code companion support — same auth,
same billing pool, same prompt-cache economics as interactive `tokenpak claude`.

---

## How it works

OpenClaw's gateway makes Anthropic Messages API calls through its embedded
runner. TokenPak slots in as the gateway's upstream proxy:

```
OpenClaw embedded agent
  └─▶ http://127.0.0.1:8766          (TokenPak proxy)
        └─▶ subprocess: claude CLI    (Claude Code companion path)
              └─▶ api.anthropic.com   (Claude Max OAuth)
```

For the `tokenpak-claude-code` provider (Claude Max OAuth path), TokenPak
spawns the local `claude` CLI per request. For `tokenpak-anthropic` and
`tokenpak-openai-codex`, TokenPak rewrites credentials in-flight and
byte-forwards to the provider's API.

---

## Install

A one-shot installer wires the integration into OpenClaw's systemd unit:

```bash
# Place the installer where openclaw-gateway can find it
install -m 0755 tokenpak-inject.sh ~/.local/bin/

# Drop a systemd override that runs it before the gateway starts
mkdir -p ~/.config/systemd/user/openclaw-gateway.service.d
cat > ~/.config/systemd/user/openclaw-gateway.service.d/tokenpak-inject.conf <<'EOF'
[Service]
ExecStartPre=/home/sue/.local/bin/tokenpak-inject.sh
EOF

systemctl --user daemon-reload
```

Then, on the next gateway start, `tokenpak-inject.sh` mutates
`~/.openclaw/openclaw.json` to:

- Add `tokenpak-*` provider entries pointing at `http://localhost:8766`.
- Mirror `auth.profiles` so existing OAuth credentials apply to the
  `tokenpak-*` mirror entries.
- Stamp the `X-TokenPak-Backend: claude-code` header on the
  `tokenpak-claude-code` provider so TokenPak's bridge recognises the
  intent.
- Sync the Codex JWT (when `~/.codex/auth.json` is present).
- Back up the previous config to `openclaw.json.tokenpak-backup`.

The script is **idempotent** — safe to re-run any number of times.

---

## Self-healing on every gateway restart

`tokenpak-inject.sh` runs as `ExecStartPre=` on the gateway service. That
means:

- If anything overwrites the config (a manual edit, a config migration,
  or an `openclaw doctor --repair`), the next gateway restart re-injects
  the TokenPak entries without any user action.
- The `tokenpak-*` providers and the `X-TokenPak-Backend` header are
  authoritative on every start. Don't edit them by hand — they'll be
  overwritten.
- If you want to tune model lists or auth profiles, edit
  `tokenpak-inject.sh` (the canonical source) and the next restart picks
  up your change.

---

## `openclaw doctor` compatibility

Running `openclaw doctor` (or `doctor --repair`) is **safe** alongside
TokenPak:

| What `tokenpak-inject.sh` writes | `openclaw doctor` behaviour |
|---|---|
| `tokenpak-*` provider entries in `models.providers` | Preserved — match the standard provider shape |
| `X-TokenPak-Backend: claude-code` header on the provider | Preserved — custom headers are not validated |
| `tokenpak-*:manual` auth profiles | Preserved — match the standard auth shape |
| `models.mode: "merge"` | Preserved — official schema field |
| Per-model `contextWindow` overrides (1M / 200k assignments) | May be normalised by `--repair` |
| `agents.defaults.contextPruning` ratios + `compaction` block | Preserved — official schema fields |
| `agents.defaults.contextTokens: 1_000_000` | Preserved — optional official field |

If `openclaw doctor --repair` normalises the per-model `contextWindow`
values, it's transient — the next gateway restart re-runs
`tokenpak-inject.sh` and they're restored automatically.

!!! warning "Don't expect `$include` indirection to survive doctor"
    OpenClaw's config writer (in `io-y3Az_Onx.js::writeConfigFile`) reads
    the snapshot, expands all `$include` directives, applies any patch,
    and writes the **expanded** result back. The `$include` directive
    itself is not preserved. So sidecar config files referenced via
    `$include` get baked inline on the first write-back — and the
    sidecar becomes orphaned. The `ExecStartPre=` re-injection pattern
    is the only resilient strategy on current OpenClaw releases (≥ v2026.3).

---

## Per-model context windows are dynamic

TokenPak v1.3.22+ resolves per-model context windows from each provider's
own `/v1/models` API at runtime. You don't maintain a hand-written list
anywhere. The cache lives at `~/.tokenpak/model_context_cache.json` and
refreshes every 24h, with fail-open semantics on registry misses.

This means: when Anthropic releases a new model, the next cache refresh
picks it up automatically. If the proxy's model registry doesn't have an
entry for a model, TokenPak skips the per-model context-cap validation
and lets the upstream return its native error — never a TokenPak block.

---

## Troubleshooting

### `LLM request rejected: You're out of extra usage`

You're on the Claude Code OAuth path but missing one of the headers
Anthropic uses to identify Claude Code traffic for the Max billing pool.
TokenPak v1.3.18+ injects all of:

- `Authorization: Bearer <claude-cli-oauth>`
- `anthropic-beta: claude-code-20250219,oauth-2025-04-20` (merged with caller's betas)
- `anthropic-dangerous-direct-browser-access: true`
- `User-Agent: claude-cli/<probed-version> (external, cli)`
- `x-app: cli`
- `X-Claude-Code-Session-Id: <stable-uuid>`

If you're seeing this error on TokenPak v1.3.18+, check that
`~/.claude/.credentials.json` has a current `claudeAiOauth.accessToken`
(run `claude` interactively once to refresh).

### `🧹 Compacting context...` fires every turn

That's OpenClaw's own context pruning, not Claude Code's compaction.
The thresholds live in `~/.openclaw/openclaw.json` under
`agents.defaults.contextPruning` and `agents.defaults.compaction`.

Recommended for Claude-Code-parity behaviour (added by hand or via your
own automation — `tokenpak-inject.sh` does not touch these fields):

```json5
{
  "agents": {
    "defaults": {
      "contextTokens": 1000000,
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "7d",
        "keepLastAssistants": 50,
        "softTrimRatio": 0.95,
        "hardClearRatio": 0.98
      },
      "compaction": {
        "mode": "safeguard",
        "reserveTokensFloor": 24000,
        "maxHistoryShare": 0.85,
        "memoryFlush": {"enabled": false}
      }
    }
  }
}
```

These keys are part of OpenClaw's official schema, so `openclaw doctor`
preserves them. Picking near-1.0 ratios with a 7d TTL effectively
delegates compaction to Claude Code's native (in-CLI) compaction, which
fires only near the model's actual wall.

### `LLM request timed out`

If your conversation is on a 200k-context model (Haiku, older Claude)
and the payload exceeds 200k tokens, TokenPak v1.3.22+ returns a clean
`HTTP 413 context_overflow` before spawning the subprocess. OpenClaw's
overflow recovery then compacts and retries cleanly — much faster than
the alternative (round-trip to Anthropic, fail, compact, retry).

If you see `LLM request timed out` on a model that should fit, check
`journalctl --user -u tokenpak-proxy.service` for the `[INJECT]` line —
it tells you which provider was selected and whether subprocess
dispatch fired.

### Bypass / debug knobs

| Env var | Effect |
|---|---|
| `TOKENPAK_CREDENTIAL_INJECTION=0` | Disable header rewriting (Codex + Anthropic-api paths) |
| `TOKENPAK_COMPANION_SUBPROCESS=0` | Force byte-forward instead of subprocess for Claude Code |
| `TOKENPAK_BRIDGE_CONTEXT_CHECK=0` | Skip per-model context cap validation |
| `TOKENPAK_BRIDGE_DISABLE_PROMPT_CACHE=1` | Disable prompt cache (debugging only — kills cache hits) |
| `TOKENPAK_BRIDGE_COMPANION=1` | Load full tokenpak-companion profile in subprocess (heavier) |
| `TOKENPAK_DUMP_HEADERS=1` | Log inbound + outbound headers (auth redacted) for diagnostics |
| `TOKENPAK_SESSION_MAPPER=0` | Disable conversation-fingerprint session mapping |

---

## Uninstall

A companion script reverts the integration cleanly:

```bash
# Preview what will change without touching anything
tokenpak-uninstall.sh --dry-run

# Revert openclaw config + remove the systemd drop-in (keeps tokenpak-proxy running)
tokenpak-uninstall.sh

# Full teardown: also stop the proxy + purge cache files
tokenpak-uninstall.sh --stop-proxy --purge-caches --yes
```

### What `tokenpak-uninstall.sh` does

1. **Reverts `~/.openclaw/openclaw.json`.** Two paths:
   - **Preferred — clean revert from pre-install backup.** The first run
     of `tokenpak-inject.sh` writes a one-time
     `~/.openclaw/openclaw.json.pre-tokenpak-backup` snapshot of the
     user's clean config. The uninstaller restores this byte-for-byte
     when present.
   - **Fallback — in-place strip.** If no pre-install backup exists
     (e.g. install pre-dates the backup feature), the uninstaller
     removes only the entries `tokenpak-inject.sh` would have added:
     `tokenpak-*` providers, `tokenpak-*:*` auth profiles, `tokenpak-*`
     entries from `auth.order`, and `tokenpak-*` model references in
     allowlist arrays. Everything else stays untouched.
2. **Removes the systemd drop-in** at
   `~/.config/systemd/user/openclaw-gateway.service.d/tokenpak-inject.conf`,
   so re-injection does not happen on the next gateway restart.
3. **Optionally** stops + disables `tokenpak-proxy.service` (`--stop-proxy`).
4. **Optionally** purges TokenPak's local caches (`--purge-caches`):
   `model_context_cache.json`, `session_map.db`.

The script always writes `*.uninstall-rollback` snapshots before destructive
edits so you can recover the post-install state if something goes wrong.

### Manual re-restart of the gateway

OpenClaw's gateway unit has `RefuseManualStop=yes`, so `systemctl --user
restart openclaw-gateway.service` is refused. After the uninstall:

```bash
kill $(systemctl --user show openclaw-gateway.service -p MainPID --value)
# systemd auto-respawns; new gateway picks up the reverted config
```

### Verifying

```bash
# Should print 0 (or only stray references unrelated to tokenpak-inject)
grep -c tokenpak ~/.openclaw/openclaw.json

# Should be empty
ls ~/.config/systemd/user/openclaw-gateway.service.d/tokenpak-inject.conf 2>/dev/null

# Optional: confirm proxy is down (if you used --stop-proxy)
systemctl --user is-active tokenpak-proxy.service
```

### Re-installing

Re-running `tokenpak-inject.sh` (manually or via re-installing the systemd
drop-in) restores everything. The uninstall is fully reversible — no
state is destroyed beyond what the user opts in to with `--purge-caches`.
