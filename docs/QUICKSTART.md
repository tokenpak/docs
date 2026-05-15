# TokenPak Quickstart — First Savings in 5 Minutes

Get TokenPak running and see your first cost savings in under 5 minutes.

## 1. Install

```bash
pip install tokenpak
```

Requires **Python 3.10+** (classifiers declare 3.10–3.13; on 3.13, the optional `tree-sitter-languages` wheel is unavailable and affected features gracefully degrade).

Verify your installation works:

```bash
tokenpak --help
tokenpak status
```

## 2. One-command setup

The interactive wizard detects your API keys, picks a compression profile, writes `~/.tokenpak/config.yaml`, and starts the proxy:

```bash
tokenpak setup
```

The wizard:

1. Scans your environment for `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`.
2. Asks which provider to proxy + which compression profile (minimal / balanced / aggressive).
3. Writes config, launches the proxy on `127.0.0.1:8766`, and prints next steps.

If you prefer manual configuration, `tokenpak start` brings the proxy up with defaults.

## 3. Point your client at the proxy

Per-client integration is a **one env-var change**. `tokenpak integrate <client>` auto-wire is on the roadmap; until then, set one of these:

### Anthropic SDK / `anthropic` Python client

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8766
```

Then use the SDK normally. TokenPak's proxy forwards your real `ANTHROPIC_API_KEY` upstream without storing it.

### OpenAI SDK / any OpenAI-compatible client

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8766
```

### Claude Code (TUI / CLI)

Claude Code reads `ANTHROPIC_BASE_URL` from the environment the same as the SDK. Start Claude Code after setting the env var and it will route through TokenPak automatically.

On provider-cached flows like Claude Code, observed incremental savings can be lower than on direct-API workloads — the provider's own prompt cache already absorbs most of the token pool. TokenPak optimizes the user-controlled portion. See the [Savings reporting](SAVINGS.md) page for the full framing.

### Aider, Cursor, Continue.dev, Cline

These accept an `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` override via their config file or environment — consult the tool's own docs for the exact setting. The common pattern is "override the base URL; TokenPak is drop-in compatible."

### Direct Python with the SDK

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://127.0.0.1:8766",
    api_key="your-anthropic-key"
)
```

## 4. Verify it's working

```bash
tokenpak status
```

You should see the proxy up, request count climbing, and per-session compression metrics.

Check health:

```bash
curl http://127.0.0.1:8766/health
```

Expected response: `{"status": "healthy"}`.

## 5. See your savings

After a handful of real requests through the proxy:

```bash
tokenpak savings
tokenpak cost --week
```

The local web dashboard at **`http://127.0.0.1:8766/dashboard`** visualizes cost + savings over time (also reachable via `tokenpak dashboard`).

### How much to expect

TokenPak's savings depend on your integration path — we don't collapse this into a single number because that would be dishonest.

- **Direct API calls, CLI tools, SDK integrations, and any uncached workload:** the compression pipeline operates on the full token pool; observed savings routinely reach **90%+** on realistic agent-style prompts. The CI-pinned floor (`make benchmark-headline` in the OSS repo) asserts ≥30% on a fixture; that's the minimum promise, not the ceiling.
- **Provider-cached flows (Claude Code and similar):** the provider's own prompt cache already absorbs most of the token pool. TokenPak only optimizes the user-controlled portion, so incremental savings can be a few percent of total spend. This isn't TokenPak failing — it's an honest division of labor with the provider.

If you're evaluating TokenPak, start with a direct-API workload to see the pipeline's actual effectiveness, then layer in your cached flows to see the marginal contribution on top.

## 6. Keep it running

For continuous savings, keep the proxy running in the background. The `tokenpak setup` wizard already launches it detached. If you stopped it:

```bash
tokenpak start                    # foreground
# or, detached:
nohup tokenpak start > ~/.tokenpak/proxy.log 2>&1 &
echo $! > ~/.tokenpak/proxy.pid
```

To stop:

```bash
tokenpak stop
# or, if detached via nohup:
kill $(cat ~/.tokenpak/proxy.pid)
```

### Run as a systemd user service (optional)

For persistent daemonization on Linux, example unit file in the OSS repo under `examples/systemd/tokenpak.service`.

## Non-localhost access (LAN exposure)

If you want to expose the proxy to other machines on your LAN, set an auth token:

```bash
export TOKENPAK_PROXY_AUTH_TOKEN=$(openssl rand -hex 32)
tokenpak start
```

Non-localhost clients must then include `X-TokenPak-Auth: <your-token>` on every request. Localhost is always allowed; the proxy auth token is stripped before anything is forwarded upstream (the SC+1 I5 conformance gate enforces this).

## Next steps

- **Tune compression** — `tokenpak recipe --help` for custom compression recipes.
- **Monitor savings** — dashboard at `http://127.0.0.1:8766/dashboard`.
- **Route-class policies** — `tokenpak/services/policy_service/presets/*.yaml` in the OSS repo ship per-client policies (Claude Code variants, Anthropic SDK, OpenAI SDK, generic).
- **Spend Guard** — `tokenpak budget --help` to configure rolling per-agent and per-fleet caps. The pre-send circuit breaker blocks runaway requests before they hit the provider.

## Troubleshooting

**"Connection refused" on `http://127.0.0.1:8766`**

- Verify the proxy is running: `tokenpak status`.
- Check port 8766 isn't in use: `lsof -i :8766`.
- Re-run `tokenpak start` (or the wizard via `tokenpak setup`).

**"API key invalid" errors**

- Ensure your provider key is set: `echo $ANTHROPIC_API_KEY`.
- TokenPak is transparent — your API key must be valid upstream.

**No savings showing after a few requests**

- Check `tokenpak status` — it should show request count + token metrics.
- If the proxy is correctly receiving traffic but savings look low, verify your workload path. Provider-cached flows (Claude Code) show lower incremental gains (see [Savings reporting](SAVINGS.md)).
- First request is always uncached; give it a few more.

**Wizard prints "No API keys detected"**

- Set at least one of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY` before running `tokenpak setup`.
