---
title: "Beta Onboarding"
---

# Beta Onboarding

Welcome to the TokenPak OSS beta. This page is the fastest path from "I heard about it" to "I'm running it and sending useful feedback."

## Who this beta is for

- Developers running LLM agent workflows daily (Claude Code, Cursor, Aider, Cline, Continue, Codex).
- Anyone building on the Anthropic, OpenAI, or LiteLLM SDKs whose API bills are starting to show.
- Engineers who want a transparent, local layer for compression / routing / cost tracking — not a hosted SaaS.
- OSS contributors who'd rather file an issue than wait for a vendor roadmap.

You don't need to use agents to benefit — any uncached LLM workload sees Prompt Packing in action. Agent workloads simply have more room to compress.

## Install

```bash
pip install tokenpak
tokenpak --version    # expect: tokenpak 1.20.0
tokenpak setup        # interactive wizard
```

`tokenpak setup` scans your environment for `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GOOGLE_API_KEY`, asks which provider to proxy, picks a compression profile, writes `~/.tpk/config.yaml` (or `~/.tokenpak/config.yaml` on systems that already have the legacy directory), and starts the proxy on `127.0.0.1:8766`.

Point your existing client at the proxy:

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8766
# or, for OpenAI-compatible clients:
export OPENAI_BASE_URL=http://127.0.0.1:8766
```

Claude Code, Cursor, Aider, Cline, and Continue all honor the same env vars. Full per-client patterns: [Quickstart](QUICKSTART.md).

## Trust posture

TokenPak runs locally. Your prompts and credentials stay in your environment and the provider flow you already use — they are not sent to TokenPak-operated infrastructure. Configuration and the local SQLite ledger live under `~/.tpk/` (canonical) or `~/.tokenpak/` (legacy fallback). See the [tokenpak.ai privacy page](https://tokenpak.ai/compliance/privacy/) for the full disclosure of optional escape-hatch flags.

## First-run smoke test (≈5 minutes)

```bash
# 1. Proxy is up
tokenpak status
curl http://127.0.0.1:8766/health        # expect: {"status": "ok", ...}

# 2. Make a real request through your usual client (any LLM call counts)
#    e.g. run one Claude Code prompt, one Cursor question, one curl to /v1/messages

# 3. See savings on the local ledger
tokenpak savings
tokenpak cost --week

# 4. Optional: open the local dashboard
tokenpak dashboard                       # opens TUI + serves web view on 8766/dashboard
```

If `tokenpak status` shows the proxy up and your request count climbing, you're set. If not, jump to [Troubleshooting](troubleshooting.md) before filing an issue — most common symptoms are covered there.

## Recommended workflows to test

These are the workflows where beta feedback is most valuable. Pick whichever matches your daily work:

1. **Direct-API agent loop** — any code that makes a sequence of LLM calls (LangChain, LlamaIndex, your own loop). Highest savings; easiest to compare before / after.
2. **Coding assistant** — Claude Code, Cursor, Aider, Cline, Continue. Run a real task end to end (open a feature branch, ask for a refactor, iterate). Note: provider-cached flows show lower incremental gains than direct-API; this is expected, and `tokenpak savings` will distinguish proxy-caused saves from provider cache hits.
3. **Long multi-turn session** — extended chat or pair-programming session where the context keeps growing. Prompt Packing's value compounds over a session.
4. **CLI / SDK script** — short Python or shell scripts that hit the LLM API directly. Cleanest case to measure compression because there's no provider-cache muddle.
5. **Spend Guard** — set a deliberate low cap and trigger the pre-send 402: `tokenpak budget --help` for knobs. Worth verifying behavior in your environment before relying on it.
6. **Vault indexing** — point `tokenpak index <dir>` at a project and try `tokenpak search "<query>"`. We want to know if results match what you'd expect.

## What savings to expect

TokenPak's headline benchmark is a deterministic reduction pinned to a CI agent-style fixture (a blocking check on every PR; reproduce with `make benchmark-headline`). On favorable uncached workloads it can reach **up to** 90%+; provider-cached flows like Claude Code show lower incremental gains. `tokenpak savings` separates proxy saves from provider cache hits.

If you're evaluating TokenPak, start with a direct-API workload to see the pipeline's actual effectiveness, then layer in your cached flows to see the marginal contribution on top.

## Known limitations

Read the full list before reporting: [Known Limitations](KNOWN_LIMITATIONS.md).

Highlights:

- The OSS beta ships the **Pak recall data plane** only. Scoring, ranking, and assembly enforcement are planned, not shipped — `severity = block` flags are stored but not enforced by OSS.
- Storage path is migrating from `~/.tokenpak/` (legacy) to `~/.tpk/` (canonical). Both work; fresh installs land on `~/.tpk/`.
- Several CLI command families (`fleet`, `macro`, `template`, `recipe`, `audit`, `agent`, `trigger`, `retrieval`, `goals`) are functional but their surfaces may change during beta. Stable verbs are listed in Known Issues.
- TokenPak is a local proxy. There is no SaaS, hosted dashboard, license server, team workspace, or shared cloud component in the beta. This is the trust-posture commitment, not a feature gap.

## Reporting issues

- **Bugs / regressions / crashes**: [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues) — please use the bug-report template. Include `tokenpak --version`, your OS, Python version, and reproduction steps.
- **Feature ideas / questions**: [github.com/tokenpak/tokenpak/discussions](https://github.com/tokenpak/tokenpak/discussions).
- **Beta-experience feedback** (overall): use the beta-feedback issue template on the same tracker.
- **Documentation gaps**: PRs against [github.com/tokenpak/docs](https://github.com/tokenpak/docs) are welcome. Small fixes get reviewed quickly.

A good first issue is one that includes the exact command you ran, what you expected, and what actually happened — with the relevant slice of `tokenpak doctor` output if anything looks off.

Thanks for testing.
