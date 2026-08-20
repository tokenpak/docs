---
title: "Known Limitations — OSS beta"
rung: 2
audience: Developers evaluating or running the TokenPak OSS beta who want an honest account of what isn't production-quality yet.
updated: 2026-08-20
status: current
---

# Known Limitations — OSS beta

This page documents current, honest limitations of the **OSS beta**
(`pip install tokenpak`, **v1.20.0**). If a capability described elsewhere in
these docs isn't shipping the way the rest of the docs imply, it shows up
here — that is the point of this page. Each entry states what's limited,
whether it's an intentional scope choice or a known defect, the honest
current behavior, a workaround if one exists, and the condition under which
the entry will be retired or updated.

If you hit something not listed here, file it at
[github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues).

---

## Storage path migration in progress

**Status:** intentional migration-safety behavior; affects fresh installs only.

**What:** the canonical local-storage path is `~/.tpk/`. Existing installs
continue to read and write wherever they already live and are **not**
migrated automatically.

**Current behavior — resolution order:**

1. `$TOKENPAK_HOME` (operator override)
2. whichever home already **holds state**, canonical preferred
3. `~/.tpk/` if it exists (canonical default)
4. `~/.tokenpak/` if it exists (legacy fallback — zero-touch upgrade)
5. `~/.tpk/`

Resolving on which home *holds state* (not mere directory existence) is what
keeps an upgrade safe: a `~/.tpk/` created as a side effect can't silently
take over an install whose state lives in `~/.tokenpak/`. A *new* install
always starts canonical — TokenPak will not begin one in the legacy
directory. An *existing* legacy install stays put until moved explicitly.
The resolver never creates directories on its own. Some docs and examples
still reference `~/.tokenpak/`; both paths work today.

**Workaround:** run `tokenpak config migrate` to move an existing legacy
install to the canonical path explicitly.

**Retirement condition:** retires when automatic zero-touch migration ships
for all installs, or the legacy `~/.tokenpak/` fallback is formally
deprecated and removed in a future major version. Neither is committed to a
version yet.

---

## Pak scoring, ranking, and assembly are not in the OSS beta

**Status:** by design — a deliberate OSS/Pro boundary, not a temporary gap.

**What:** the OSS recall layer is a transparent data plane. It persists
Paks, reason codes, and risk flags, and exposes them via the
`tokenpak.companion.recall` Python API and `tokenpak pak inspect`.

**Current behavior:** the OSS package does **not** rank Paks by reason-code
scores, refuse to assemble when a Pak carries `severity = block`, reorder
Paks according to `ordering_hints` during assembly, or implement
`tokenpak pak plan` / `assemble` / `validate` verbs. `tokenpak pakplan`
ships `preview`, `explain`, and `report` (read-only) only. `severity=block`
flags are stored but not enforced by OSS. See the
[Recall overview](recall/index.md) for the full OSS-vs-planned split.

**Workaround:** read Pak reason codes and risk flags directly and enforce
policy in your own calling code if you need `severity=block` respected
today.

**Retirement condition:** this entry is updated (not silently dropped) if
and when the scoring/ranking/assembly-enforcement engine ships to the OSS
surface. No version is committed; until then this is a durable OSS/Pro
split, not a bug.

---

## Not every CLI command is part of the supported surface

**Status:** classified, and the classification is enforced by a test.

**What:** the parser registers 90 commands as of v1.20.0. Forty are the
supported beta surface; the other fifty are reachable but not verified for
this release, and each one carries a written reason for its exclusion.

**Current behavior:** the distinction is not advisory — an allowlist names
the supported set, a test pairs it against the live parser, and both
default help surfaces list only supported commands, so a verb cannot
quietly enter or leave the product. **Excluded is not removed**: every
excluded command still parses and still runs; what it loses is a place in
default discovery. Some are excluded because they target operators rather
than a single machine (`fleet`, `audit`, `agent`, `compliance`); some spend
real money or need live provider traffic (`benchmark`, `calibrate`); some
are genuinely unfinished and say so (`watch` points at `dashboard`; `last`
is a stub).

**Workaround:** run `tokenpak help --all` to see every registered command
with its exclusion reason.

**Retirement condition:** this entry's counts are updated at any release
that changes the registered/supported split; the classification mechanism
itself is a durable design choice with no planned removal.

---

## Default port standardization

**Status:** historical doc residue; largely already cleaned up.

**What:** the proxy default port is **`8766`**. Older doc snippets and
code examples from before standardization referenced `8000`.

**Current behavior:** no remaining `8000` default-port reference was found
in this docs tree as of v1.20.0. All current configurations and the setup
wizard write `8766`. A config file saved locally from before the
standardization may still contain `8000`.

**Workaround:** if you have an old config from before the standardization,
rerun `tokenpak setup` to refresh it.

**Retirement condition:** safe to remove once no incoming reports reference
a lingering `8000` default from an old local config; kept for continuity
until then.

---

## Coverage gate is advisory

**Status:** intentional during beta (tracked as issue #161).

**What:** the repository's ≥80% coverage gate runs with
`continue-on-error: true` at the step level.

**Current behavior:** a threshold breach is visible in workflow logs but
does not block a merge.

**Workaround:** none needed by package users; contributors should still
treat coverage regressions seriously even though CI will not block on them.

**Retirement condition:** flips back to blocking once the ratchet baseline
lands (tracked in issue #161).

---

## No managed cloud / hosted offering

**Status:** by design — a durable trust-posture commitment, not a feature
gap.

**What:** TokenPak is a **local proxy**. There is no SaaS, hosted
dashboard, license server, team workspace, SSO, or shared cloud component
in the OSS beta.

**Current behavior:** the package runs on `127.0.0.1` and only talks to the
upstream LLM provider you configure.

**Workaround:** not applicable — this is the product's trust posture, not a
gap to work around.

**Retirement condition:** none. Changing this would require a strategic
decision to add hosted/cloud components, which is not planned.

---

## Legacy per-model pricing display path bypasses the shared pricing catalog

**Status:** known gap, tracked as a follow-on (not fixed in v1.20.0).

**What:** one legacy, disconnected, hand-maintained per-model pricing
display path — an analytics cost lookup distinct from the canonical pricing
catalog that v1.20.0 refreshed (current-generation Claude model rows priced,
a stale Haiku row corrected) — does not yet delegate to the shared catalog.

**Current behavior:** this legacy path can still render an incorrect dollar
figure for models outside its own hardcoded list. Unlike the catalog-backed
paths, it never abstains — it does not fall back to an explicit
unavailable state when it doesn't recognize a model.

**Workaround:** treat catalog-backed cost/savings surfaces
(`tokenpak savings`, `tokenpak cost`, the session-economics trip computer)
as authoritative. If a dollar figure from another display looks off for a
newer model, cross-check against those.

**Retirement condition:** retires when this legacy path is migrated to
delegate to the shared pricing catalog. No version is committed yet.

---

## Calibrated forecast bands stay in a "learning" state for cold model×effort cells

**Status:** intentional — a deliberate fail-safe, not a bug.

**What:** the session-economics trip computer's calibrated
remaining-consumption forecast (added in v1.20.0) requires a given
model×effort cell to clear a measured-history trust floor before it
produces a numeric coverage/forecast band.

**Current behavior:** cold cells report an explicit `learning` state rather
than a number. The underlying observed facts (spent tokens, cost, burn)
stay visible and accurate even while the forecast itself is still learning.
Stale or unknown provider rates leave USD unavailable while token-based
ranges stay intact. Measured walk-forward coverage is reported as observed,
never asserted as nominal, and drifting coverage triggers a refit rather
than a relabel.

**Workaround:** none needed — this is working as designed. Use a
session/model/effort combination with enough history if a calibrated band
is needed immediately.

**Retirement condition:** none. Never fabricating a forecast the data
doesn't support is a durable design commitment, not scheduled for removal.

---

## When NOT to use TokenPak

TokenPak is not the right fit for every workload today. Stating that
plainly is a feature, not a weakness:

- **Pure byte-pass or already-minimal-context workloads.** If there's
  little redundant or compressible context in your requests, there's
  little for Prompt Packing to reduce — you'll see minimal-to-no savings to
  show for it.
- **Teams that need a hosted, multi-tenant, or centrally-managed proxy
  today.** TokenPak is a local, single-machine process. There is no
  SaaS, hosted control plane, or shared cloud component in the OSS beta
  (see "No managed cloud / hosted offering" above).
- **Workloads that require enforced Pak scoring, ranking, or
  `severity=block` assembly gating today.** OSS ships the recall data
  plane only; enforcement is not part of the OSS beta surface (see above).
- **Anyone who needs a stable, docs-committed CLI surface across all 90
  registered commands.** Only the 40 classified commands are the
  supported beta surface; the rest may change without notice.

---

## Reporting beta issues

- **Crashes / regressions:** [github.com/tokenpak/tokenpak/issues](https://github.com/tokenpak/tokenpak/issues) — please include OS, Python version, TokenPak version (`tokenpak --version`), and reproduction steps.
- **Feature requests:** [github.com/tokenpak/tokenpak/discussions](https://github.com/tokenpak/tokenpak/discussions).
- **Documentation gaps:** PRs against [github.com/tokenpak/docs](https://github.com/tokenpak/docs) are welcome.
