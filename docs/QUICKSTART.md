---
title: "TokenPak quickstart: first savings in 5 minutes"
rung: 1
audience: Developers installing TokenPak for the first time.
updated: 2026-08-20
status: current
---

# TokenPak quickstart: first savings in 5 minutes

This quickstart is for developers installing TokenPak for the first time. Get
the proxy running and see your first cost savings in under 5 minutes.

## Install

```bash
pip install tokenpak
```

Requires **Python 3.10+** (classifiers declare 3.10–3.13; on 3.13, the optional `tree-sitter-languages` wheel is unavailable and affected features gracefully degrade).

Verify your installation works:

```bash
tokenpak --help
tokenpak status
```

## Configure and start

The interactive wizard detects optional provider API keys, picks a compression
profile, and writes the configuration. New installs use `~/.tpk/config.yaml`;
an existing install keeps using its state-bearing `~/.tpk/` or legacy
`~/.tokenpak/` home. Add `--start` to launch the proxy after configuration:

```bash
tokenpak setup --start
```

The wizard:

1. Scans your environment for optional `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY` values. If none are present, setup continues normally for clients that already have their own credentials.
2. Asks for the port and compression profile (minimal / balanced / aggressive). A default provider is requested only when direct provider keys were detected.
3. Writes config, launches the proxy on `127.0.0.1:8766` because `--start` was
   supplied, and prints next steps.

To configure without starting anything, run `tokenpak setup`; start the proxy
later with `tokenpak start`.

## Point your client at the proxy

Run `tokenpak integrate <client>` to print the current setup steps. For clients
that support managed configuration, `tokenpak integrate <client> --apply` can
write the configuration; instruction-only targets continue with printed
guidance. The manual environment-variable paths below remain valid:

### Anthropic SDK and the `anthropic` Python client

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8766
```

Then use the SDK normally. TokenPak's proxy forwards your real `ANTHROPIC_API_KEY` upstream without storing it.

### OpenAI SDK and compatible clients

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8766/v1
```

### Claude Code with TUI or CLI

Claude Code reads `ANTHROPIC_BASE_URL` from the environment the same as the SDK. Start Claude Code after setting the env var and it will route through TokenPak automatically.

On provider-cached flows like Claude Code, observed incremental savings can be lower than on direct-API workloads — the provider's own prompt cache already absorbs most of the token pool. TokenPak optimizes the user-controlled portion. See the [Savings reporting](SAVINGS.md) page for the full framing.

### Codex CLI with OAuth

If Codex is already signed in, no OpenAI or Anthropic API key and no explicit
model override are required:

```bash
tokenpak codex
```

TokenPak reuses Codex's existing OAuth request path and preserves the model
selected by Codex. See [Use TokenPak with Codex CLI](guides/codex.md) for the
temporary-session behavior when another Codex session is already running.

### Other client tools

These accept an `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` override via their config file or environment — consult the tool's own docs for the exact setting. The common pattern is "override the base URL; TokenPak is drop-in compatible."

### Direct Python with the SDK

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="your-anthropic-key"
)
```

## Verify it works

```bash
tokenpak status
```

You should see the proxy up, request count climbing, and per-session compression metrics.

Check health:

```bash
curl http://127.0.0.1:8766/health
```

The expected response includes `{"status": "ok", "version": "1.20.0"}`.

## See your savings

After a handful of real requests through the proxy:

```bash
tokenpak savings
tokenpak cost --week
```

The local web dashboard at **`http://127.0.0.1:8766/dashboard`** visualizes cost + savings over time (also reachable via `tokenpak dashboard`).

### How much to expect

TokenPak's savings depend on your integration path — we don't collapse this into a single number because that would be dishonest.

- **Direct API calls, CLI tools, SDK integrations, and any uncached workload:** the compression pipeline operates on the full token pool; on favorable uncached workloads savings can reach **up to** 90%+. Reproduce the headline benchmark with `make benchmark-headline`; measure your own with `tokenpak savings`.
- **Provider-cached flows (Claude Code and similar):** the provider's own prompt cache already absorbs most of the token pool. TokenPak only optimizes the user-controlled portion, so incremental savings can be a few percent of total spend. This isn't TokenPak failing — it's an honest division of labor with the provider.

If you're evaluating TokenPak, start with a direct-API workload to see the pipeline's actual effectiveness, then layer in your cached flows to see the marginal contribution on top.

## Keep it running

For continuous savings, use TokenPak's managed background process. Both
`tokenpak setup --start` and `tokenpak start` launch it detached:

```bash
tokenpak start
```

Stop the process through the same lifecycle manager:

```bash
tokenpak stop
```

## Network access: LAN exposure

If you intentionally expose the proxy to other machines on your LAN, opt in to
a non-loopback bind and set a proxy auth token:

```bash
export TOKENPAK_BIND_ADDRESS=0.0.0.0
export TOKENPAK_PROXY_AUTH_TOKEN="$(openssl rand -hex 32)"
tokenpak start
```

Non-localhost clients must then include
`Authorization: Bearer <TOKENPAK_PROXY_AUTH_TOKEN>` on every request. A remote
request is rejected with `403` if the server has no proxy auth token configured,
or `401` if the Bearer credential is missing or wrong. Localhost is always
allowed. The proxy credential is stripped before forwarding; supply any direct
provider credential separately, such as with `x-api-key`.

## Next steps

- **Tune compression** — `tokenpak recipe --help` for custom compression recipes.
- **Monitor savings** — dashboard at `http://127.0.0.1:8766/dashboard`.
- **Spend Guard** — `tokenpak budget --help` to configure rolling per-agent and per-fleet caps. The pre-send circuit breaker blocks runaway requests before they hit the provider.

## Troubleshooting

**"Connection refused" on `http://127.0.0.1:8766`**

- Verify the proxy is running: `tokenpak status`.
- Check port 8766 isn't in use: `lsof -i :8766`.
- Re-run `tokenpak start` (or the wizard via `tokenpak setup --start`).

**"API key invalid" errors**

- Ensure your provider key is set: `echo $ANTHROPIC_API_KEY`.
- TokenPak is transparent — your API key must be valid upstream.

**No savings showing after a few requests**

- Check `tokenpak status` — it should show request count + token metrics.
- If the proxy is correctly receiving traffic but savings look low, verify your workload path. Provider-cached flows (Claude Code) show lower incremental gains (see [Savings reporting](SAVINGS.md)).
- First request is always uncached; give it a few more.

**Wizard prints "No API keys detected"**

- This is informational. Continue without a key when your client already has
  its own authenticated session, such as Codex OAuth. For direct provider API
  traffic, set only the relevant `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or
  `GOOGLE_API_KEY` and rerun setup.
