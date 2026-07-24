---
title: "Known Issues — OSS beta"
---

# Known Issues — OSS beta

This page tracks current limitations of the **OSS beta** (`pip install tokenpak`, v1.14.0). The intent is **beta honesty**: if a documented capability isn't shipping the way the rest of the docs imply, it shows up here.

If you hit something not listed here, file it at [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues).

---

## Storage path migration in progress

**Status:** affects fresh installs only.

The canonical local-storage path is `~/.tpk/`. Existing installs continue to read from `~/.tokenpak/` (the legacy fallback) and are not migrated automatically. The CLI resolves paths in this order:

1. `$TOKENPAK_HOME` (operator override)
2. `~/.tpk/` (canonical default)
3. `~/.tokenpak/` (legacy fallback — only when `~/.tpk/` is absent and legacy exists)

If you started with TokenPak before May 2026, you can keep using `~/.tokenpak/`. Fresh installs will create `~/.tpk/`. Some docs and examples still reference `~/.tokenpak/`; both paths work today.

---

## Pak scoring, ranking, and assembly are not in the OSS beta

**Status:** by design.

The OSS recall layer is a transparent data plane — it persists Paks, reason codes, and risk flags, and exposes them via the `tokenpak.companion.recall` Python API and `tokenpak pak inspect`. The OSS package **does not**:

- Rank Paks by reason-code scores.
- Refuse to assemble when a Pak carries `severity = block`.
- Reorder Paks according to `ordering_hints` during assembly.
- Implement `tokenpak pak plan` / `assemble` / `validate` verbs.

`tokenpak pakplan` ships `preview`, `explain`, and `report` (read-only). The scoring engine and autonomous injection pipeline are planned for a later release and are not part of the OSS beta surface.

See the [Recall overview](recall/index.md) for the full OSS-vs-planned split.

---

## Some documented CLI commands are experimental

**Status:** stability flag missing.

The CLI exposes ~47 top-level commands. The following families are functional but their surface, output format, and flag set may change without notice during the beta:

- `tokenpak fleet ...` — multi-machine orchestration
- `tokenpak macro ...` — user-defined YAML macros
- `tokenpak template ...` — template expansion
- `tokenpak recipe ...` — recipe management
- `tokenpak audit ...` — audit log management
- `tokenpak agent ...` — agent coordination locks
- `tokenpak trigger ...` — event triggers
- `tokenpak retrieval ...` — hybrid retrieval debug
- `tokenpak goals ...` — savings goals

Treat anything outside the stable verbs (`start`/`stop`/`status`/`savings`/`cost`/`setup`/`doctor`/`config`/`index`/`search`/`stats`/`models`/`budget`/`dashboard`/`update`/`version`) as subject to change.

---

## Default port standardization

**Status:** docs cleanup landing in beta.

The proxy default port is **`8766`**. Some older doc snippets and code examples reference `8000` (an earlier default). All current configurations and the setup wizard write `8766`. If you have an old config from before the standardization, rerun `tokenpak setup` to refresh it.

---

## Coverage gate is advisory

**Status:** intentional during beta.

The repository's coverage gate is currently advisory (`continue-on-error: true` at the step level). Threshold breach is visible in workflow logs but does not block merges. This will flip back to blocking once the ratchet baseline lands.

---

## No managed cloud / hosted offering

**Status:** by design.

TokenPak is a **local proxy**. There is no SaaS, hosted dashboard, license server, team workspace, SSO, or shared cloud component in the OSS beta. The package runs on `127.0.0.1` and only talks to the upstream LLM provider you configure. This is the trust-posture commitment, not a feature gap.

---

## Reporting beta issues

- **Crashes / regressions:** [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues) — please include OS, Python version, TokenPak version (`tokenpak --version`), and reproduction steps.
- **Feature requests:** [github.com/tokenpak/tokenpak/discussions](https://github.com/tokenpak/tokenpak/discussions).
- **Documentation gaps:** PRs against [github.com/tokenpak/docs](https://github.com/tokenpak/docs) are welcome.
