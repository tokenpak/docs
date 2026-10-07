---
title: "Beta Onboarding"
---

# Beta Onboarding

Welcome to the TokenPak OSS beta. This page is the fastest path from "I heard about it" to "I'm running it and sending useful feedback."

## Who this beta is for

- Developers and tech leads running long coding-agent sessions in Claude Code or Codex, the first-class integrations.
- Anyone building on the Anthropic SDK, OpenAI SDK, or LiteLLM (tested adapters) whose API bills are starting to show.
- Engineers who want a transparent, local layer for request records, explicit context tools, and cost tracking — not a hosted SaaS.
- OSS contributors who'd rather file an issue than wait for a vendor roadmap.

Cursor, Cline, Continue and Aider are compatibility targets, not yet independently verified. You are welcome to try them and report what you find; their guides describe an expected setup.

You don't need to use an agent to try TokenPak: any LLM request you send through the proxy is recorded. The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved.

## Install

```bash
pip install tokenpak
tokenpak --version    # expect: tokenpak 1.30.3
tokenpak setup --start    # interactive wizard; --start also launches the proxy
```

`tokenpak setup` scans your environment for `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY`, asks which provider to proxy, picks a compression profile, and writes `~/.tpk/config.yaml` (or `~/.tokenpak/config.yaml` on systems that already have the legacy directory). With `--start`, it also starts the proxy on `127.0.0.1:8766`.

Point your existing client at the proxy:

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8766
# or, for OpenAI-compatible clients:
export OPENAI_BASE_URL=http://127.0.0.1:8766/v1
```

Codex launches through `tokenpak codex`. Cursor, Cline, Continue and Aider are compatibility targets, not yet independently verified. Full per-client patterns: [Quickstart](QUICKSTART.md).

## Trust posture

TokenPak runs locally. Your prompts and credentials stay in your environment and the provider flow you already use — they are not sent to TokenPak-operated infrastructure. By default the proxy talks only to the upstream provider you configure; optional features can make other network requests, such as an update check against pypi.org (TokenPak asks first) and an anonymous metrics heartbeat (off by default). Configuration and the local SQLite ledger live under `~/.tpk/` (canonical) or `~/.tokenpak/` (legacy fallback). See the [tokenpak.ai privacy page](https://tokenpak.ai/compliance/privacy/) for the privacy details.

## First-run smoke test (≈5 minutes)

```bash
# 1. Proxy is up
tokenpak status
curl http://127.0.0.1:8766/health        # expect: {"status": "ok", ...}

# 2. Make a real request through your usual client (any LLM call counts)
#    e.g. run one Claude Code prompt, one Codex prompt, one curl to /v1/messages

# 3. See usage and savings on the local ledger (zero tokens saved is a valid result)
tokenpak savings
tokenpak cost --week

# 4. Optional: open the local dashboard
tokenpak dashboard                       # opens TUI + serves web view on 8766/dashboard
```

If `tokenpak status` shows the proxy up and your request count climbing, you're set. If not, jump to [Troubleshooting](troubleshooting.md) before filing an issue — most common symptoms are covered there.

## Recommended workflows to test

These are the workflows where beta feedback is most valuable. Pick whichever matches your daily work:

1. **Direct-API agent loop** — any code that makes a sequence of LLM calls (Anthropic SDK, OpenAI SDK, LiteLLM, your own loop). Easiest to compare before / after.
2. **Coding assistant** — Claude Code or Codex (first-class); Cursor, Cline, Continue and Aider are compatibility targets, not yet independently verified. Run a real task end to end (open a feature branch, ask for a refactor, iterate). Inspect recorded usage with `tokenpak savings`; inspect provider-cache versus TokenPak attribution with `tokenpak status --tip-cache`.
3. **Long multi-turn session** — extended chat or pair-programming session where the context keeps growing. Watch measured usage, burn and runway in the session footer or `tokenpak status`.
4. **CLI / SDK script** — short Python or shell scripts that hit the LLM API directly. Inspect recorded usage with `tokenpak savings`.
5. **Spend Guard** — set a deliberate low cap and trigger the pre-send 402: `tokenpak budget --help` for knobs. Worth verifying behavior in your environment before relying on it.
6. **Vault indexing** — point `tokenpak index <dir>` at a project and try `tokenpak search "<query>"`. We want to know if results match what you'd expect.

## What savings to expect

TokenPak reports what it measured on your own traffic and does not promise a savings figure. The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved; explicit context tools can reduce eligible content. `make benchmark-headline` exercises a fixed fixture, and its result is not a default-proxy savings receipt. Inspect recorded usage with `tokenpak savings`; inspect provider-cache versus TokenPak attribution with `tokenpak status --tip-cache`.

If you're evaluating TokenPak, start with a real session in Claude Code or Codex, read the receipt and `tokenpak status`, and then try explicit context tools on your own workload.

## Known limitations

Read the full list before reporting: [Known Limitations](KNOWN_LIMITATIONS.md).

Highlights:

- The OSS beta ships the **Pak recall data plane** only. Scoring, ranking, and assembly enforcement are planned, not shipped — `severity = block` flags are stored but not enforced by OSS.
- Storage path is migrating from `~/.tokenpak/` (legacy) to `~/.tpk/` (canonical). Both work; fresh installs land on `~/.tpk/`.
- Several CLI command families (`fleet`, `macro`, `template`, `recipe`, `audit`, `agent`, `trigger`, `retrieval`, `goals`) are functional but their surfaces may change during beta. Stable verbs are listed in Known Issues.
- TokenPak is a local proxy. The OSS package has no SaaS, hosted dashboard, team workspace, or shared cloud component. This is the trust-posture commitment, not a feature gap.

## Reporting issues

- **Bugs / regressions / crashes**: [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues) — please use the bug-report template. Include `tokenpak --version`, your OS, Python version, and reproduction steps.
- **Feature ideas / questions**: [github.com/tokenpak/tokenpak/discussions](https://github.com/tokenpak/tokenpak/discussions).
- **Beta-experience feedback** (overall): use the beta-feedback issue template on the same tracker.
- **Documentation gaps**: PRs against [github.com/tokenpak/docs](https://github.com/tokenpak/docs) are welcome. Small fixes get reviewed quickly.

A good first issue is one that includes the exact command you ran, what you expected, and what actually happened — with the relevant slice of `tokenpak doctor` output if anything looks off.

Thanks for testing.
