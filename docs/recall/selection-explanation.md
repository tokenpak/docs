# Deterministic Recall Pak selection (OSS-visible signals)

This page explains how an OSS caller can deterministically pick which Paks to include in a Context Package using only signals visible through the OSS recall store. It is a **narrative + pseudo-code reference**, not a Pro scorer.

The Pro daemon ships a tuned scorer with extension points, capture pipelines, and runtime ranking. OSS is the data plane: it persists Paks, FTS shadows, reason codes, and risk flags; it does not impose a ranking algorithm. If you want recall to be reproducible and inspectable without Pro, the signals below give you everything you need to write your own selector.

---

## What "deterministic" means here

A recall selector is **deterministic** if, given the same recall store state and the same query inputs, it returns the same ordered Pak list every run. Two requirements:

1. **Pure function of OSS-visible state.** No clock-based jitter, no random sampling, no cached priors from a previous run.
2. **Stable tiebreak.** When two Paks tie on every other signal, the selector falls back to a deterministic ordering — `(updated_at DESC, pak_id DESC)` matches the store's natural order and is the recommended tiebreak.

Both conditions are achievable with the OSS surface alone. The pseudo-code below maintains them throughout.

---

## OSS-visible signals

Six signals are available without Pro:

| Signal | Source | What it tells you |
|---|---|---|
| **Anchor match** | Caller-supplied vs Pak metadata (project, topic, anchor fields on the Pak body) | The Pak is in-scope for the task. |
| **Recency** | `paks.updated_at` | The Pak is freshly written or recently touched. |
| **Content hash equality** | `paks.content_hash` | Two Paks carry byte-identical bodies — candidates for de-duplication. |
| **FTS hits** | `paks_fts` virtual table (`MATCH` queries on `title` + `summary`) | The Pak's text matches the query terms. |
| **Reason rows** | `pak_reason_codes` (28-code closed registry) | The caller — or an upstream stage — already recorded why this Pak is relevant. |
| **Risk severity** | `pak_risk_flags` (13-flag closed registry) | The Pak carries risk indicators that should influence inclusion or post-package review. |

The recall store exposes all six. The first four are direct columns / virtual tables on the `paks` schema; the last two are the join tables documented in [Pak Reason Codes](reason-codes.md) and [Pak Risk Flags](risk-flags.md).

---

## A minimal deterministic selector — pseudo-code

The selector takes a query (free text plus optional `project` / `pak_type` filters) and an explicit budget (`limit`). It walks the OSS signals in priority order, scores each candidate, and returns the top-`limit` Paks under a stable tiebreak.

```python
# Pure pseudo-code for documentation. Not a shipped API.

from dataclasses import dataclass
from tokenpak.companion.recall import (
    PakListFilters,
    PakRow,
    ReasonCodeEntry,
    RecallStore,
    RiskFlagEntry,
)


@dataclass(frozen=True)
class Query:
    text: str                       # FTS5 MATCH query
    project: str | None = None      # byte-literal filter (no aliasing)
    pak_type: str | None = None     # byte-literal filter
    recency_window_days: int = 30   # caller-defined; affects scoring only
    limit: int = 25                 # final selection size


@dataclass(frozen=True)
class Score:
    pak_id: str
    score: float
    risk_severities: frozenset[str]   # observability — not a kill switch in OSS


def select(store: RecallStore, q: Query) -> list[Score]:
    """Deterministic top-K Pak selection over OSS-visible signals."""

    # 1. FTS hits — the spine of the candidate set. Returns pak_ids sorted by
    #    the FTS5 ranking function; we re-sort below so the final order does
    #    not depend on FTS rank ties.
    fts_hits: dict[str, float] = _fts_query(store, q.text)

    # 2. Pull metadata for the candidate set + anything the caller-supplied
    #    filters bring in (anchor matches that don't surface in FTS).
    candidates: dict[str, PakRow] = _hydrate(store, fts_hits, q)

    # 3. Per-candidate scoring — pure function of OSS-visible state.
    scored: list[Score] = []
    for pak_id, row in candidates.items():
        s = 0.0

        # 3a. FTS contribution.
        s += fts_hits.get(pak_id, 0.0) * 1.0

        # 3b. Anchor match — caller-supplied filters that line up with row
        #     fields. project / pak_type / topic are byte-literal.
        if q.project and row.project == q.project:
            s += 0.5
        if q.pak_type and row.pak_type == q.pak_type:
            s += 0.3

        # 3c. Recency. Older Paks contribute less; nothing decays past zero.
        s += _recency_bonus(row.updated_at, q.recency_window_days)

        # 3d. Reason-code contribution. Each row contributes its weight,
        #     scaled by a stable per-category factor the caller controls.
        reason_rows: list[ReasonCodeEntry] = store.get_pak_reason_codes(pak_id)
        s += sum(_weight_for(r.reason_code) * r.weight for r in reason_rows)

        # 3e. Content-hash de-duplication. Keep the newer of any pair sharing
        #     a content_hash. (Done after this loop, see step 4.)

        # 3f. Risk flags are recorded but do not refuse inclusion in OSS.
        risk_rows: list[RiskFlagEntry] = store.get_pak_risk_flags(pak_id)
        risk_severities = frozenset(r.severity for r in risk_rows)

        scored.append(Score(pak_id=pak_id, score=s, risk_severities=risk_severities))

    # 4. Content-hash collapse: keep the most-recent Pak per content_hash.
    #    Deterministic because we tiebreak on (updated_at DESC, pak_id DESC).
    scored = _collapse_by_content_hash(scored, candidates)

    # 5. Final stable sort. Primary key: descending score. Tiebreak:
    #    descending updated_at, then descending pak_id (matches the store's
    #    natural ordering, so cursoring behaviour is consistent).
    scored.sort(
        key=lambda s: (
            -s.score,
            _row_key(candidates[s.pak_id]),
        )
    )
    return scored[: q.limit]


def _row_key(row: PakRow) -> tuple[str, str]:
    """Reverse-lexicographic key — sort puts larger strings first."""
    return (_neg(row.updated_at), _neg(row.pak_id))
```

The helpers (`_fts_query`, `_hydrate`, `_recency_bonus`, `_weight_for`, `_collapse_by_content_hash`, `_neg`) are caller-defined; their bodies are the same shape across any deterministic implementation. The point of the pseudo-code is the **signal flow**, not any specific weighting.

---

## Each signal in detail

### Anchor match

The recall store stores `project` and `topic` columns on every Pak row, plus a `pak_type` discriminator. The `PakListFilters` shape supports byte-literal filtering on `project` and `pak_type`:

```python
filters = PakListFilters(project="tokenpak", pak_type="vault", limit=100)
result = store.list_paks(filters)
```

No alias expansion, no casefolding — the column value must equal the filter exactly. Anchor matches on the Pak body itself (file paths, line ranges, identifiers) are encoded as fields on the Pak JSON and matched by the caller after `inspect`.

### Recency

`paks.updated_at` is an ISO-8601 UTC string written by `upsert_pak` on every write. The natural `list_paks` ordering is `(updated_at DESC, pak_id DESC)` — newest first, with `pak_id` as a deterministic tiebreak.

A typical recency bonus is a monotonic decay over the caller's window:

```python
def _recency_bonus(updated_at: str, window_days: int) -> float:
    age = _utc_now() - _parse_iso(updated_at)
    if age.days >= window_days:
        return 0.0
    return 1.0 - (age.total_seconds() / (window_days * 86400.0))
```

Whatever decay shape you choose, keep it a **pure function** of `updated_at` and a fixed window. Don't sample wall clock inside the inner loop; pass it in once at the top of `select()` so all candidates see the same `_utc_now()`.

### Content hash equality

`paks.content_hash` is the hex digest of the underlying Pak body. Two rows with identical `content_hash` carry identical bodies — they are de-duplication candidates. The recommended collapse rule:

> **Among rows that share a `content_hash`, keep the one with the highest `updated_at`; break ties on the highest `pak_id`.**

This is both deterministic and pak-id stable, which matters for cache reuse downstream.

### FTS hits

The `paks_fts` virtual table is an FTS5 shadow over `title` + `summary` (kept consistent by the v2 triggers). Callers query it directly:

```python
rows = store.conn.execute(
    "SELECT pak_id FROM paks_fts WHERE paks_fts MATCH ? ORDER BY rank",
    (q.text,),
).fetchall()
```

The `unicode61` tokenizer is configured with `remove_diacritics=2`, so `cafe` and `café` match the same row. Empty stores return zero rows; queries against absent terms return zero rows.

The FTS5 rank value is a sound input to your scorer. Just **re-sort after combining with non-FTS signals** — FTS rank order alone is not stable across queries that share the same primary score but differ on recency or reason rows.

### Reason rows

[`pak_reason_codes`](reason-codes.md) is observability data, not a scoring directive — but a deterministic selector can use it as one. Two common patterns:

- **Per-code weighting** — assign a stable scalar to each `reason_code` (e.g. `current_task = 1.0`, `direct_file_match = 0.7`, `stale_context = -1.0`) and sum the contributions. Keep the weights in a literal mapping; do not pull them at runtime from anywhere that can change between calls.
- **Category gating** — treat `exclude`-category codes as a hard skip for the candidate (not a hard removal — the row is still observable in the store; the selector just doesn't pick it for this query).

Both patterns stay inside the OSS surface and stay deterministic.

### Risk severity

[`pak_risk_flags`](risk-flags.md) carries the severity signal in `{info, warn, block}`. In the OSS selector:

- `info` is an observability tag — passes through into the `Score.risk_severities` field for the caller to display.
- `warn` is also a pass-through; it does not change inclusion in OSS, but a downstream reviewer surface (such as `tokenpak pak inspect`) renders it prominently.
- `block` is the one to be careful with. **OSS does not refuse to include a Pak because it carries a `block` flag.** The selector may choose to surface the flag (recommended) but must not silently drop the Pak — the receiver decides whether to refuse.

The Pro Phase 3 Context Package builder is where `block` becomes enforcement. Until then, the recommended OSS pattern is "include + flag" so the human-reviewable trace contains the data.

---

## Worked example — a minimum scoring config

A working OSS selector configuration that runs entirely on the signals above:

```python
REASON_WEIGHTS = {
    # task / authority
    "current_task":          1.0,
    "mandatory":             1.0,
    "acceptance_criteria":   0.9,
    "user_pinned":           1.0,
    "standard_applies":      0.9,
    "governance_constraint": 1.0,
    "risk_relevant":         0.8,
    "prior_success_pattern": 0.7,
    # match
    "agent_role_match":      0.6,
    "task_type_match":       0.6,
    "direct_file_match":     0.8,
    "direct_test_match":     0.8,
    "dependency_match":      0.5,
    "workflow_relevant":     0.6,
    # recency
    "recently_modified":     0.4,
    "recent_failure_link":   0.9,
    # shape
    "compressed_summary_available": 0.4,
    "large_raw_context":     0.2,
    "available_on_request":  0.3,
    "stable_context":        0.5,
    "reusable_context":      0.5,
    "cache_ordering_candidate": 0.5,
    # exclude (negative — drop or strongly penalise)
    "low_task_match":         -1.0,
    "unrelated_domain":       -1.0,
    "stale_context":          -1.0,
    "duplicate_context":      -0.5,
    "excluded_by_budget":     -0.5,
    "excluded_by_policy":     -1.0,
}
```

Three properties make this config deterministic:

1. **It is a literal** — no runtime lookup, no environment variable, no per-Pak override.
2. **It covers every catalogued code** — no surprises when a future Pak adds a new reason row.
3. **Negative codes are explicit** — `exclude`-category codes drop scores below the inclusion threshold, which is the documented OSS contract.

If a downstream caller wants different weights, they ship their own literal. The recall store is unchanged.

---

## What this is **not**

- **Not a Pro scorer.** The Pro daemon's scorer admits ranked alternatives, online tuning, fleet-wide priors, and feedback loops. None of that is in this page.
- **Not a CLI verb.** OSS does not ship `tokenpak pak select`. Selection is caller code; the recall store is the data surface.
- **Not enforcement.** Risk severity `block` does not refuse inclusion in OSS. The selector may surface it; the receiver decides.

---

## Related

- [Recall store API](recall-store-api.md) — the read/write surface the selector calls into.
- [Pak Reason Codes](reason-codes.md) — the catalogue + per-code guidance.
- [Pak Risk Flags](risk-flags.md) — the severity catalogue and the `block` observability invariant.
- [`tokenpak pak inspect`](inspect-and-explain.md) — the surface a human uses to see what the selector picked, and why.
