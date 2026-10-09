# TokenPak Configuration Reference

TokenPak is configured via environment variables (or a `~/.tokenpak/config.yaml` file). Environment variables always take precedence over config-file values.

> **Single source of truth:** the complete, authoritative list of every `TOKENPAK_*` variable — names, defaults, and types — lives in **[Environment Variables](env-vars.md)**. This page covers *how* configuration is applied plus the security-relevant defaults worth calling out; it intentionally does **not** duplicate the full variable table (which previously drifted out of sync with it).

---

## API Keys

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Optional | Needed only for direct Anthropic API-key traffic |
| `OPENAI_API_KEY` | Optional | Needed only for direct OpenAI API-key traffic |
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Optional | Needed only for direct Google API-key traffic |

TokenPak itself does not require an API key or an explicit model selection.
Direct API clients still need the credential required by their upstream
provider. Already-authenticated clients can keep using their existing session
credentials; for example, `tokenpak codex` reuses Codex OAuth and preserves the
client's selected or default model.

---

## Bind address & network exposure (security-relevant)

By default TokenPak binds the proxy to **`127.0.0.1` (localhost only)** — it is **not** reachable from other machines out of the box.

| Variable | Default | Description |
|---|---|---|
| `TOKENPAK_BIND_ADDRESS` | `127.0.0.1` | Proxy listen address. Set to `0.0.0.0` **only** when you intentionally need LAN/Docker access — and pair it with `TOKENPAK_PROXY_KEY` and dashboard auth. |
| `TOKENPAK_PORT` | `8766` | Proxy listen port. |

Binding to `0.0.0.0` exposes the proxy on all network interfaces — do this deliberately and with authentication enabled. See [Security](SECURITY.md).

---

## How configuration is applied

**Environment variables** (highest precedence):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export TOKENPAK_PORT=8766
tokenpak serve
```

**Config file** — `~/.tokenpak/config.yaml`:
```yaml
server:
  port: 8766
  host: "127.0.0.1"
```
Any environment variable overrides the matching config-file value.

---

## The TokenPak home folder

TokenPak keeps its state, such as the request ledger, spend-cap and telemetry
history, journals and `home-migrated.json`, in one home folder. New installs use
`~/.tpk`. An install that predates it keeps using `~/.tokenpak`. If you set
`TOKENPAK_HOME`, that folder is the home. Run `tokenpak home path` to see which
one is in use.

If both `~/.tokenpak` and `~/.tpk` hold state, `tokenpak doctor` warns "split
home: both homes hold state". Since 1.31.0, every write goes to `~/.tpk` in that
layout, so history left in `~/.tokenpak` can look reset. Merge it with
`tokenpak home migrate`:

```bash
tokenpak home migrate            # print the plan; changes nothing
tokenpak home migrate --apply    # write the merge
tokenpak home migrate --json     # machine-readable plan
```

The merge is backup-first: every changed target is saved under
`~/.tpk/backups/home-migrate-<time>/`. A file that differs keeps the `~/.tpk`
copy, and the older one is saved beside it as `<name>.legacy`. Databases are
merged row by row. `~/.tokenpak` is never changed or deleted. The command
refuses while the proxy or a companion session is in use, and a successful
`--apply` writes a receipt, `home-migrated.json`, in `~/.tpk`. `tokenpak doctor`
then reports `migrated on <time>`. See the
[1.31.0 upgrade guide](upgrading.md#merge-the-older-home-folder-with-tokenpak-home-migrate)
for the full behavior.

---

## Common recipes

**Disable compaction (pure passthrough proxy):**
```bash
export TOKENPAK_COMPACT=0
```

**Debug mode (verbose tracing):**
```bash
export TOKENPAK_TRACE=1
export TOKENPAK_REQUEST_LOGGER=1
```

---

*See [Quick Start](QUICKSTART.md) for setup and **[Environment Variables](env-vars.md)** for the complete `TOKENPAK_*` reference.*
