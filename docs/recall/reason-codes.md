# Pak Reason Codes

The `pak_reason_codes` table on a TokenPak recall store carries the **why** behind every Pak that a recall pipeline considers — selected, deferred, or excluded. The 28 codes catalogued below are the closed registry shipped with TIP-1.0 (`pak-reason-codes-v1`).

In OSS, these codes are an **observability tag set**. The Pak is selected (or rejected) by the caller's own logic; the reason rows let humans, dashboards, and audit trails see why each decision was made. Scoring against these codes — turning them into an actual ranker — is Pro daemon behaviour.

- **Machine-readable source of truth:** [`pak-reason-codes-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-reason-codes-v1.json) on the registry.
- **OSS persistence:** `pak_reason_codes` join table (recall storage v3 migration).
- **OSS access:** `RecallStore.set_pak_reason_codes` / `get_pak_reason_codes` — see [Recall store API](recall-store-api.md).
- **Closed catalogue:** new codes require an additive (Class B) amendment. Pro-only extensions live in a sibling `pak-reason-codes-v1.pro.json` overlay and are never required by OSS receivers.

---

## Shape of one row

Each row attaches a single `(pak_id, reason_code)` pair, with an optional `weight` in `[0.0, 1.0]` and a creation timestamp.

```python
from tokenpak.companion.recall import RecallStore, ReasonCodeEntry

with RecallStore.open() as store:
    store.set_pak_reason_codes(
        "vault:auth-pattern#a1b2c3",
        [
            ReasonCodeEntry(reason_code="current_task",       weight=1.0),
            ReasonCodeEntry(reason_code="standard_applies",   weight=0.8),
            ReasonCodeEntry(reason_code="direct_file_match",  weight=0.6),
        ],
    )
```

`weight` is an OSS-side hint, not a ranker input. Callers (and Pro scorers downstream) decide how to interpret it; OSS persists it byte-for-byte and validates the range. Defaults to `1.0` when omitted.

The row set is **replaced** on every call to `set_pak_reason_codes`: re-calling with the same payload is a no-op in final state; calling with `[]` clears the codes for that Pak.

---

## The 28 codes by category

The schema groups codes into six categories. `exclude` codes mark a Pak as **rejected from the package** — they are observability tags, not enforcement (OSS does not refuse to include a Pak because an `exclude` code was attached; the caller decides).

### `task` — the current task explicitly references this Pak

| Code | When to populate | Example weight |
|---|---|---|
| `current_task` | Caller's request mentions this Pak by ID, anchor, or title. | `1.0` |
| `mandatory` | Marked as required by caller config, governance, or fleet policy. | `1.0` |
| `acceptance_criteria` | Pak carries acceptance criteria the task must satisfy. | `0.8`–`1.0` |
| `user_pinned` | Caller pinned this Pak explicitly (CLI flag, config entry). | `1.0` |

**Typical payload:**

```python
[
    ReasonCodeEntry("current_task", 1.0),
    ReasonCodeEntry("acceptance_criteria", 0.9),
]
```

### `match` — the Pak relates to the task by topic, role, or scope

| Code | When to populate | Example weight |
|---|---|---|
| `agent_role_match` | Pak's topic/project matches the requesting agent's role. | `0.6`–`0.9` |
| `task_type_match` | Pak relates to the current task type (implement / review / plan / etc.). | `0.5`–`0.8` |
| `direct_file_match` | Pak's anchors reference a file in the task scope. | `0.7`–`1.0` |
| `direct_test_match` | Pak's anchors reference a test file in the task scope. | `0.7`–`1.0` |
| `dependency_match` | Pak references a dependency of the task scope (import graph, vendored module). | `0.4`–`0.7` |
| `workflow_relevant` | Pak relates to the current workflow type (release, hotfix, audit, etc.). | `0.5`–`0.8` |

**Typical payload:**

```python
[
    ReasonCodeEntry("agent_role_match", 0.7),
    ReasonCodeEntry("direct_file_match", 0.9),
    ReasonCodeEntry("workflow_relevant", 0.6),
]
```

### `recency` — the Pak is fresh or links to a recent event

| Code | When to populate | Example weight |
|---|---|---|
| `recently_modified` | Pak's `updated_at` falls within a caller-defined recency window. | `0.4`–`0.7` |
| `recent_failure_link` | Pak links to a recent failure event (CI failure, incident, defect). | `0.7`–`1.0` |

### `authority` — the Pak carries enforcement weight

| Code | When to populate | Example weight |
|---|---|---|
| `standard_applies` | Pak references a ratified standard that applies to the task. | `0.8`–`1.0` |
| `governance_constraint` | Pak is a governance pin, invariant, or canonical decision. | `1.0` |
| `risk_relevant` | Pak surfaces a risk relevant to the task (see also: [Risk flags](risk-flags.md)). | `0.7`–`1.0` |
| `prior_success_pattern` | Pak captures a prior accepted resolution to a similar task. | `0.6`–`0.9` |

### `shape` — the Pak's form affects how it should travel

| Code | When to populate | Example weight |
|---|---|---|
| `compressed_summary_available` | A compressed / summarized form is preferred over raw bytes. | `0.5`–`0.8` |
| `large_raw_context` | Raw content exceeds the package token budget; consider compression or deferral. | `0.5`–`1.0` |
| `available_on_request` | Pak is deferred but hydratable on request (lazy fetch). | `0.3`–`0.6` |
| `stable_context` | Pak content is stable across sessions; cache-friendly. | `0.6`–`1.0` |
| `reusable_context` | Pak is reusable across tasks within a project (anchor candidate). | `0.6`–`1.0` |
| `cache_ordering_candidate` | Pak is a candidate for cache-stability ordering (see [`ordering_hints`](ordering-hints-examples.md)). | `0.6`–`1.0` |

### `exclude` — the Pak was rejected from the package

| Code | When to populate | Example weight |
|---|---|---|
| `low_task_match` | Caller's match score fell below threshold. | `0.0`–`0.4` |
| `unrelated_domain` | Pak's domain (project / topic) does not match the task. | `0.0`–`0.3` |
| `stale_context` | Pak content is superseded or has aged out. | `0.0`–`0.3` |
| `duplicate_context` | Pak duplicates another included Pak (content-hash match). | `0.0`–`0.2` |
| `excluded_by_budget` | Pak would push the package over its token budget. | `0.0`–`0.5` |
| `excluded_by_policy` | Pak hits a policy gate (sensitive list, scope rule, permission). | `0.0`–`0.2` |

!!! note "`exclude` is observability, not enforcement"
    Attaching `excluded_by_budget` to a Pak does **not** prevent OSS code paths from reading the Pak back out of the store. The code records the caller's intent so the rejection is auditable. The same applies to `excluded_by_policy`: it is a tag, not a kill-switch.

---

## When to populate

Populate reason codes at the point a caller decides to include or exclude a Pak from a Context Package. Typical write points:

- **At pak ingestion** — a capture pipeline that promotes a vault block or interaction trace into the recall store can attach `stable_context`, `reusable_context`, or `governance_constraint` at write time.
- **At package assembly** — the caller's recall pipeline calls `set_pak_reason_codes` once it has decided which Paks belong in the package. This is the typical "selection trace" use.
- **At post-hoc audit** — a reviewer can re-call `set_pak_reason_codes` to amend reasons retroactively. The replace-on-write semantic makes this safe; the join table never accumulates orphan rows.

---

## Reading codes back

Codes are returned in ascending `reason_code` order so callers see a deterministic listing across calls:

```python
with RecallStore.open() as store:
    codes = store.get_pak_reason_codes("vault:auth-pattern#a1b2c3")
    for entry in codes:
        print(f"  {entry.reason_code:30s}  weight={entry.weight:.2f}")
```

Unknown `pak_id` returns `[]` rather than raising.

---

## Related

- [Pak Risk Flags](risk-flags.md) — the parallel `pak_risk_flags` catalogue with severity intent.
- [Recall store API](recall-store-api.md) — full read / write surface for both join tables.
- Registry schema: [`pak-reason-codes-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-reason-codes-v1.json)
