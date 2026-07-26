---
title: "Known Issues — OSS beta"
---

# Known Issues — OSS beta

This page tracks current limitations of the **OSS beta** (`pip install tokenpak`, v1.16.0). The intent is **beta honesty**: if a documented capability isn't shipping the way the rest of the docs imply, it shows up here.

If you hit something not listed here, file it at [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues).

---

## Storage path migration in progress

**Status:** affects fresh installs only.

The canonical local-storage path is `~/.tpk/`. Existing installs continue to read and write where they already live and are not migrated automatically. Resolution order:

1. `$TOKENPAK_HOME` (operator override)
2. whichever home already **holds state**, canonical preferred
3. `~/.tpk/` if it exists (canonical default)
4. `~/.tokenpak/` if it exists (legacy fallback — zero-touch upgrade)
5. `~/.tpk/`

Step 2 is what keeps an upgrade safe. Resolving on mere directory *existence* meant a `~/.tpk/` created as a side effect could take over an install whose state lived in `~/.tokenpak/`, and every subsequent read would come back empty — on a Pro install, that read back as Free. Resolution now follows the state, so an existing install is never moved out from under its own readers.

A *new* install always starts canonical: TokenPak will not begin one in the legacy directory. An *existing* legacy install stays put until `tokenpak config migrate` moves it explicitly.

The resolver never creates directories — reading where your state lives cannot bring a home into being. Some docs and examples still reference `~/.tokenpak/`; both paths work today.

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

## Not every command the CLI accepts is part of the supported surface

**Status:** classified, and the classification is enforced.

The parser registers 90 commands. Forty are the supported beta surface; the other fifty are reachable but not verified for this release, and each one carries a written reason for its exclusion.

The distinction is not advisory. An allowlist names the supported set, a test pairs it against the live parser, and both default help surfaces list only supported commands — so a verb cannot quietly enter or leave the product.

**Excluded is not removed.** Every excluded command still parses and still runs; what it loses is a place in default discovery. To see them with their reasons:

```bash
tokenpak help --all
```

Some are excluded because they are aimed at operators rather than a single machine (`fleet`, `audit`, `agent`, `compliance`). Some spend real money or need live provider traffic (`benchmark`, `calibrate`). Some are genuinely not finished, and say so — `watch` describes itself as unimplemented and points at `dashboard`; `last` is a stub with no implementation behind it. The reason is attached to each, so "this is ready" is distinguishable from "this is reachable" without guessing.

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
