# `tokenpak pak inspect` — semantics today, and as recall data populates

The Phase 1 OSS surface for examining a Pak is `tokenpak pak inspect`. It is read-only, it works without the Pro daemon for Vault Paks, and it returns the same payload shape as the corresponding HTTP endpoint so dashboards, fleet automation, and human reviewers see one canonical structure.

This page documents:

1. What `tokenpak pak inspect` surfaces **today** (in Phase 1 OSS).
2. What it surfaces **as `pak_reason_codes` and `pak_risk_flags` rows populate** — i.e. how the inspector becomes an explanation surface without new verbs being added.
3. The `tokenpak pak status` diagnostic, and how to read its output.

The lane is **inspect refinement, not new verbs**. No `plan`, `assemble`, `validate`, or `explain` subcommand is being introduced; the goal is that `inspect` becomes informationally richer as the join tables fill in.

---

## What `inspect` returns today

`tokenpak pak inspect <pak-id-or-file>` resolves a Pak ID (or reads a Pak file from disk) and prints its metadata. Two surfaces:

- **Text mode (default)** — human-readable, suitable for terminal output.
- **JSON mode (`--json`)** — exactly the same payload as `GET /pak/v1/inspect/<pak-id>`. Field names, types, and key ordering are stable across the two surfaces by design.

### Text output

```text
$ tokenpak pak inspect vault:auth-pattern#a1b2c3
Pak vault:auth-pattern#a1b2c3
────────────────────────────────────────
  type        : vault
  title       : router-not-vault credential architecture
  status      : active
  authority   : llm_generated
  confidence  : 0.8
  source      : vault (doc)
  source_hash : 0123456789abcdef…
  created_at  : 2026-05-09T14:22:11Z
  project     : tokenpak

Summary:
  Single-refresh-owner invariant across providers; cohabitation flagged.
```

### JSON output

```json
{
  "pak_id": "vault:auth-pattern#a1b2c3",
  "pak_type": "vault",
  "title": "router-not-vault credential architecture",
  "status": "active",
  "authority": "llm_generated",
  "confidence": 0.8,
  "source": {
    "platform": "vault",
    "source_type": "doc",
    "source_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "created_at": "2026-05-09T14:22:11Z"
  },
  "scope": {
    "project": "tokenpak"
  },
  "summary": "Single-refresh-owner invariant across providers; cohabitation flagged."
}
```

### What `inspect` does **not** do today

Phase 1 `inspect` is intentionally narrow:

- It resolves Vault Paks via the OSS adapter. Other Pak subtypes (interaction, decision, recall, handoff) return a "Pro daemon required" envelope with exit code 1.
- It returns metadata. It does not return Pak body bytes, anchors, or referenced source content — `tokenpak pak export` is the read path for content.
- It does not yet read the `pak_reason_codes` or `pak_risk_flags` join tables. That refinement is documented below.

### Errors

`inspect` exits with code 1 on the user-facing errors below and emits a JSON error envelope under `--json`:

| Error | JSON `error` field | Text |
|---|---|---|
| Vault block not indexed | `pak_not_found` | `vault block not indexed: <pak-id>` |
| Pak file missing | `file_not_found` | `file not found: <path>` |
| Pak file unparseable | `invalid_pak_file` | `cannot parse Pak file: <reason>` |
| Non-Vault subtype on Phase 1 OSS | `not_implemented` (`reason: pro_daemon_required`) | "requires the Pro daemon — non-Vault subtypes are encrypted at rest" |

Exit code 2 is reserved for argparse usage errors (handled by argparse itself).

---

## How `inspect` becomes an explanation surface

The recall storage v3 migration added two join tables: [`pak_reason_codes`](reason-codes.md) and [`pak_risk_flags`](risk-flags.md). Once a recall pipeline writes rows to those tables for a given `pak_id`, the same Pak can be inspected with two additional, additive sections — without a new CLI verb.

The contract is:

- **Field shape is additive.** When reason / risk rows exist for the inspected Pak, they appear as new top-level keys in the JSON payload. When they don't, the keys are **omitted** — receivers that don't know about reason codes or risk flags see byte-identical output to today.
- **Field source is the join table.** The inspector reads `pak_reason_codes` and `pak_risk_flags` via `RecallStore.get_pak_reason_codes` / `get_pak_risk_flags`. No new state, no new files.
- **No enforcement on `block`.** Inspect-time output for a Pak with a `severity="block"` row is the row itself — surfaced for the human reader. OSS does not refuse to inspect, export, or otherwise read the Pak (see [`risk-flags.md`](risk-flags.md#oss-does-not-refuse-on-severity--block)).
- **Closed catalogues.** The inspector renders catalogue codes / flags verbatim from the join table; it does not invent new strings. A reason code or risk flag that is not in the registry is still rendered (the runtime does not enforce the catalogue), but a registry-aware validator will surface that mismatch.

### Anticipated JSON shape with recall rows present

```json
{
  "pak_id": "vault:auth-pattern#a1b2c3",
  "pak_type": "vault",
  "title": "router-not-vault credential architecture",
  "status": "active",
  "authority": "llm_generated",
  "confidence": 0.8,
  "source": { "...": "..." },
  "scope": { "project": "tokenpak" },
  "summary": "...",

  "reason_codes": [
    { "code": "current_task",     "weight": 1.0 },
    { "code": "standard_applies", "weight": 0.9 },
    { "code": "direct_file_match","weight": 0.7 }
  ],
  "risk_flags": [
    { "flag": "governance_applies",    "severity": "warn" },
    { "flag": "cache_sensitive_ordering","severity": "info" }
  ]
}
```

Both arrays are sorted ascending on the natural key (`code` / `flag`) so the output is deterministic across runs.

### Anticipated text shape

```text
$ tokenpak pak inspect vault:auth-pattern#a1b2c3
Pak vault:auth-pattern#a1b2c3
────────────────────────────────────────
  type        : vault
  title       : router-not-vault credential architecture
  status      : active
  authority   : llm_generated
  ... (existing fields) ...

Reason codes:
  current_task              weight=1.00   (task)
  direct_file_match         weight=0.70   (match)
  standard_applies          weight=0.90   (authority)

Risk flags:
  ⚠ governance_applies      (warn)
  ℹ cache_sensitive_ordering (info)
```

The category column on reason codes (`task / match / recency / authority / shape / exclude`) is looked up from the registry, not stored in the join table — the inspector renders it for readability.

### Backward compatibility

`tokenpak pak inspect` output is part of the OSS public surface. The additive shape above preserves all existing JSON keys; new keys (`reason_codes`, `risk_flags`) are introduced only when the join tables have content. A consumer that pins to today's JSON shape continues to parse correctly when reason / risk rows are absent.

If you depend on this surface in scripts, treat both new keys as optional and absent-by-default.

---

## `tokenpak pak status` — the diagnostic surface

`tokenpak pak status` is the always-works diagnostic: it runs whether or not the Pro daemon is installed, and reports MultiPak readiness. JSON mode (`--json`) mirrors `GET /pak/v1/status`.

```text
$ tokenpak pak status
MultiPak Pro Phase 1 status
───────────────────────────
✅ Daemon state           : active
⚠️ multipak.enabled       : false
⚠️ Pak store present      : false
📦 Vault Paks indexed     : 142
📦 Promotion candidates   : 7
```

| Field | What it says | Where it comes from |
|---|---|---|
| `daemon_state` | `active`, `degraded`, or `unavailable` | `tokenpak.licensing.daemon_probe.detect_daemon_state()` |
| `multipak_enabled` | The `multipak.enabled` config flag (default `False`) | `tokenpak doctor` / config loader |
| `pak_store_present` | Whether the Pro multipak state directory exists | filesystem check |
| `vault_paks_indexed` | How many vault blocks the bridge currently has indexed | vault bridge |
| `promotion_candidates` | How many journal entries are flagged as Pak promotion candidates | `companion.journal.pak_aware` |

Exit code is always `0` — status is informational, not pass/fail.

### What `status` tells you about recall data

`status` is intentionally not a per-Pak surface. It reports **inventory** (how many Vault Paks are indexed, how many promotion candidates are queued) but does not aggregate reason-code or risk-flag counts. If you want a per-Pak view of reason / risk rows, call `inspect`; if you want a programmatic walk of the join tables, use `RecallStore.get_pak_reason_codes` / `get_pak_risk_flags` directly.

---

## Verbs that are **not** in this lane

Two verbs are mentioned only to be explicitly out of scope:

- **`explain`** — Phase 1 OSS does not ship a `tokenpak pak explain` verb. The "explanation" surface is `inspect` becoming richer as the join tables populate; an `explain` verb would be a new surface and is not part of this lane.
- **`plan` / `assemble` / `validate`** — these belong to the Pro Phase 3 Context Package builder. Not in the OSS Phase 1 surface, and not added here.

The forbidden list is documented alongside the Pak lane in the protocol guide.

---

## Related

- [Pak Reason Codes](reason-codes.md) — what fields can appear under `reason_codes`.
- [Pak Risk Flags](risk-flags.md) — what fields can appear under `risk_flags`.
- [Recall store API](recall-store-api.md) — how to write the join rows that drive the additive inspector output.
- [Deterministic Recall Pak selection](selection-explanation.md) — the OSS-visible signals that motivate the recall data in the first place.
