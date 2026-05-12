# Pak Risk Flags

The `pak_risk_flags` table on a TokenPak recall store carries the **risk signal** for every Pak in a Context Package. The 13 flags catalogued below are the closed registry shipped with TIP-1.0 (`pak-risk-flags-v1`), each pinned to a fixed severity in `{info, warn, block}`.

- **Machine-readable source of truth:** [`pak-risk-flags-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-risk-flags-v1.json) on the registry.
- **OSS persistence:** `pak_risk_flags` join table (recall storage v3 migration).
- **OSS access:** `RecallStore.set_pak_risk_flags` / `get_pak_risk_flags` — see [Recall store API](recall-store-api.md).
- **Closed catalogue:** new flags require an additive (Class B) amendment. Pro-only extensions live in a sibling `pak-risk-flags-v1.pro.json` overlay and are never required by OSS receivers.

---

## OSS does not refuse on `severity = block` { #oss-does-not-refuse-on-severity--block }

This is the most important invariant on this page.

!!! warning "`block` is a data tag in OSS"
    OSS persists, exposes, inspects, exports, and validates rows with `severity="block"`. **OSS does not refuse to assemble a Context Package because a `block` flag was attached.** Refusal lives in the Pro Phase 3 Context Package builder.

    Two consequences:

    1. A caller that wants enforcement must implement it themselves or upgrade to Pro. Reading a `block` row out of the store and ignoring it is not a violation of any OSS contract.
    2. An OSS recall store with `block` rows present is a perfectly valid, byte-stable input to a Pro builder downstream. The store side is enforcement-agnostic on purpose.

This split — OSS = transparent data plane; Pro = enforcement — is intentional. It keeps the OSS surface a pure observability layer, and lets Pro upgrade enforcement semantics without changing the recall schema.

---

## Shape of one row

Each row attaches a single `(pak_id, risk_flag)` pair, with the schema-pinned severity and a creation timestamp.

```python
from tokenpak.companion.recall import RecallStore, RiskFlagEntry

with RecallStore.open() as store:
    store.set_pak_risk_flags(
        "vault:auth-pattern#a1b2c3",
        [
            RiskFlagEntry(risk_flag="governance_applies",     severity="warn"),
            RiskFlagEntry(risk_flag="cache_sensitive_ordering", severity="info"),
        ],
    )
```

The severity passed in **must** match the schema-defined severity for that flag — the registry pins each flag to one severity, and the SQL CHECK constraint accepts only `{info, warn, block}`.

The row set is **replaced** on every `set_pak_risk_flags` call: re-calling with the same payload is a no-op in final state; calling with `[]` clears the flags for that Pak.

---

## The 13 flags by severity

### `info` — observability only

| Flag | When to populate |
|---|---|
| `mandatory_context_present` | Mandatory Paks are present in the package as expected. Pairs with `mandatory_context_missing` for completeness audits. |
| `cache_sensitive_ordering` | The package contains cache-sensitive blocks; downstream re-ordering changes cache hit rate. See [`ordering_hints`](ordering-hints-examples.md). |

### `warn` — surfaces in UI / CLI output

| Flag | When to populate |
|---|---|
| `raw_logs_deferred` | A raw-log Pak was deferred; the package consumer can request hydration. |
| `full_file_deferred` | A full-file Pak was deferred; same hydration story. |
| `governance_applies` | A governance-constraint Pak is in the package; readers should treat its contents as enforced. |
| `release_rule_applies` | A release-rule Pak is in the package; readers should treat its contents as enforced. |
| `oss_pro_boundary_risk` | The package mixes OSS-safe Paks with Pro-only sources. The reader may need to suppress Pro-only data when serializing to public surfaces. |
| `network_or_egress_risk` | The package may trigger non-LLM egress consideration (URLs to fetch, credentials referenced). |
| `large_context_reduction` | The candidate set was significantly larger than the assembled package — surface this so reviewers know the recall layer made hard cuts. |
| `low_confidence_plan` | Match scores were uniformly low across candidates; consider broadening the recall query. |
| `possible_context_miss` | Coverage scoring suggests likely missing context (e.g., no Pak covers a referenced file). |
| `manual_review_recommended` | High-impact package; a human reviewer should inspect before assembly is consumed. |

### `block` — Pro-only enforcement; OSS treats as a data tag

| Flag | When to populate |
|---|---|
| `mandatory_context_missing` | A required Pak is absent from the package. OSS persists the flag and exposes it via `get_pak_risk_flags`; the Pro Phase 3 builder is the only surface that refuses to assemble on this signal. |

---

## When to populate

Populate flags at the point a caller has visibility into the risk:

- **At capture / ingestion** — when a Pak first lands in the recall store, attach intrinsic flags like `governance_applies` or `release_rule_applies`. These are static properties of the Pak itself.
- **At package assembly** — flags whose meaning depends on the whole package (`mandatory_context_present`, `mandatory_context_missing`, `large_context_reduction`, `possible_context_miss`) are written once the recall pipeline knows which Paks made the cut.
- **At review time** — a reviewer can attach `manual_review_recommended` retroactively to capture human judgment in the audit trail.

---

## Reading flags back

Flags are returned in ascending `risk_flag` order:

```python
with RecallStore.open() as store:
    flags = store.get_pak_risk_flags("vault:auth-pattern#a1b2c3")
    for entry in flags:
        marker = {"info": "ℹ", "warn": "⚠", "block": "■"}.get(entry.severity, "?")
        print(f"  {marker} {entry.risk_flag:30s}  ({entry.severity})")
```

Unknown `pak_id` returns `[]` rather than raising.

The constant `RISK_FLAG_SEVERITIES` (a `frozenset({"info", "warn", "block"})`) is exported on the recall module so callers and tests can assert against the same string set the SQL CHECK constraint enforces.

---

## Severity enforcement boundary — at a glance

| Layer | `info` | `warn` | `block` |
|---|---|---|---|
| **OSS recall store** (persist, expose, inspect, export, validate) | ✅ | ✅ | ✅ |
| **OSS package assembly** (refuse to build a package) | — | — | **no — pass-through** |
| **Pro Phase 3 Context Package builder** | surfaces | surfaces | **refuses** |

The data is the data. Only the Pro builder treats `block` as a hard stop.

---

## Related

- [Pak Reason Codes](reason-codes.md) — the parallel `pak_reason_codes` catalogue (28 codes across 6 categories).
- [Recall store API](recall-store-api.md) — full read / write surface for both join tables.
- Registry schema: [`pak-risk-flags-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-risk-flags-v1.json)
