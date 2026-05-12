# Recall Store API — reason codes & risk flags

The `RecallStore` join-table surface is the OSS read/write API for the [`pak_reason_codes`](reason-codes.md) and [`pak_risk_flags`](risk-flags.md) tables introduced in the recall storage v3 migration. This page documents the four methods, their invariants, and what each one rejects.

The executable specification — including round-trip, idempotency, FK cascade, and validation cases — lives in [`tests/companion/recall/test_reason_codes_and_risk_flags.py`](https://github.com/tokenpak/tokenpak/blob/main/tests/companion/recall/test_reason_codes_and_risk_flags.py). When this page and the test file disagree, the test file wins.

---

## Surface

```python
from tokenpak.companion.recall import (
    RecallStore,
    ReasonCodeEntry,
    RiskFlagEntry,
    RISK_FLAG_SEVERITIES,
)
```

| Method | Purpose |
|---|---|
| `RecallStore.set_pak_reason_codes(pak_id, codes, *, now=None)` | Replace the reason-code set for a Pak. |
| `RecallStore.get_pak_reason_codes(pak_id)` | Read the reason-code set, sorted ascending by code. |
| `RecallStore.set_pak_risk_flags(pak_id, flags, *, now=None)` | Replace the risk-flag set for a Pak. |
| `RecallStore.get_pak_risk_flags(pak_id)` | Read the risk-flag set, sorted ascending by flag. |

The two read methods are pure helpers — no transaction, no clamp. The two write methods are transactional **DELETE-then-INSERT** under a single `BEGIN IMMEDIATE`.

---

## Shapes

```python
class ReasonCodeEntry(NamedTuple):
    reason_code: str
    weight: float = 1.0     # required in [0.0, 1.0]


class RiskFlagEntry(NamedTuple):
    risk_flag: str
    severity: str           # one of {"info", "warn", "block"}


RISK_FLAG_SEVERITIES: frozenset[str] = frozenset({"info", "warn", "block"})
```

Both types are immutable NamedTuples; equality and ordering are structural.

---

## Round-trip — the happy path

```python
from tokenpak.companion.recall import RecallStore, ReasonCodeEntry, RiskFlagEntry

with RecallStore.open() as store:
    # The parent Pak row must exist first — FK enforcement is on.
    store.upsert_pak(
        pak_id="vault:auth-pattern#a1b2c3",
        pak_type="vault",
        source_type="doc",
        authority="llm_generated",
        title="auth pattern",
        content_hash="0123456789abcdef" * 4,
    )

    store.set_pak_reason_codes(
        "vault:auth-pattern#a1b2c3",
        [
            ReasonCodeEntry("current_task", 1.0),
            ReasonCodeEntry("standard_applies", 0.9),
        ],
    )
    store.set_pak_risk_flags(
        "vault:auth-pattern#a1b2c3",
        [
            RiskFlagEntry("governance_applies", "warn"),
        ],
    )

    codes = store.get_pak_reason_codes("vault:auth-pattern#a1b2c3")
    flags = store.get_pak_risk_flags("vault:auth-pattern#a1b2c3")

assert codes == [
    ReasonCodeEntry("current_task", 1.0),
    ReasonCodeEntry("standard_applies", 0.9),
]
assert flags == [RiskFlagEntry("governance_applies", "warn")]
```

`get_*` returns rows in ascending order on the natural key (`reason_code` / `risk_flag`) so callers see a stable listing across runs.

---

## Idempotent re-set

Calling either `set_*` method twice with the same payload leaves the join table in the same final state. The implementation is DELETE-then-INSERT inside one transaction; the second call deletes the rows the first inserted and re-inserts them with the same `(pak_id, *)` primary key.

```python
store.set_pak_reason_codes(pid, [ReasonCodeEntry("current_task", 1.0)])
store.set_pak_reason_codes(pid, [ReasonCodeEntry("current_task", 1.0)])  # no-op in final state
```

Two consequences worth knowing:

- `created_at` advances on the second call — the rows are physically new. If you depend on `created_at` for first-observation analytics, snapshot it before re-setting.
- Two concurrent writers calling `set_*` on the same `pak_id` will serialize via `BEGIN IMMEDIATE`; the **last writer wins**.

---

## Empty payload clears the prior set

Passing `[]` is the supported way to clear the join rows for a Pak without dropping the Pak itself:

```python
store.set_pak_reason_codes(pid, [])   # removes all reason rows for pid
assert store.get_pak_reason_codes(pid) == []
```

---

## FK cascade — dropping the Pak drops its join rows

Both join tables are defined with `REFERENCES paks(pak_id) ON DELETE CASCADE`, and `PRAGMA foreign_keys = ON` is set at every `RecallStore.open()`. Deleting a row from `paks` removes its reason rows and risk-flag rows in the same statement:

```python
import sqlite3

with RecallStore.open() as store:
    # ... set codes and flags ...
    store.conn.execute("DELETE FROM paks WHERE pak_id = ?", (pid,))
    store.conn.commit()

    assert store.get_pak_reason_codes(pid) == []
    assert store.get_pak_risk_flags(pid) == []
```

The reverse — inserting join rows for a `pak_id` that has no parent row in `paks` — raises `sqlite3.IntegrityError` from the FK enforcement.

---

## Validation — what `set_*` rejects before writing

Both write methods validate inputs **before** opening a transaction, so a rejected call never leaves the store in a half-written state.

### `set_pak_reason_codes`

| Input | Result |
|---|---|
| `pak_id` is empty / whitespace | `ValueError` |
| `reason_code` is empty / whitespace | `ValueError` |
| `weight` is not `int`/`float` or falls outside `[0.0, 1.0]` | `ValueError` |
| `codes` contains a duplicate `reason_code` | `ValueError` (rejected before write so the PK error doesn't mask intent) |
| `pak_id` does not exist in `paks` | `sqlite3.IntegrityError` (FK violation; raised inside the transaction, which rolls back) |

### `set_pak_risk_flags`

| Input | Result |
|---|---|
| `pak_id` is empty / whitespace | `ValueError` |
| `risk_flag` is empty / whitespace | `ValueError` |
| `severity` is not in `RISK_FLAG_SEVERITIES` | `ValueError` |
| `flags` contains a duplicate `risk_flag` | `ValueError` (before write) |
| `pak_id` does not exist in `paks` | `sqlite3.IntegrityError` (FK violation; rolls back) |

### `get_*` — never raises on input shape

`get_pak_reason_codes` and `get_pak_risk_flags` treat empty / whitespace / unknown `pak_id` as **a miss**: they return `[]` rather than raising. The schema rejects empty primary keys at write time, so an empty-key lookup is unambiguously empty.

---

## Concurrency

- `PRAGMA journal_mode = WAL` is set at open so readers don't block writers.
- `PRAGMA busy_timeout = 5000` covers transient lock contention; concurrent `set_*` calls on the same `pak_id` serialize cleanly.
- Both `set_*` methods open a `BEGIN IMMEDIATE` transaction (write lock acquired up front), commit on success, and roll back on any exception. The FTS5 triggers from earlier migrations fire under the same transaction.

---

## What this surface does **not** do

- **No ranking, scoring, or selection.** Reading a Pak's reason codes does not change what `list_paks` returns; the catalogue is observability, not a filter. Selection is a caller concern; see [Deterministic Recall Pak selection](selection-explanation.md) for an OSS-visible-signals walkthrough.
- **No `severity="block"` enforcement.** OSS persists and surfaces `block` rows; refusal lives in the Pro Phase 3 Context Package builder. See [Pak Risk Flags](risk-flags.md#oss-does-not-refuse-on-severity--block).
- **No catalogue mutation.** New reason codes or risk flags require a registry amendment; the runtime does not enforce the catalogue itself (it accepts any snake_case string), but a JSON Schema validator against the registry is the recommended pre-write gate.

---

## Related

- [Pak Reason Codes](reason-codes.md) — catalogue + per-code guidance.
- [Pak Risk Flags](risk-flags.md) — catalogue + severity boundary.
- [Deterministic Recall Pak selection](selection-explanation.md) — OSS-visible signals you can rank against.
- Tests: [`tests/companion/recall/test_reason_codes_and_risk_flags.py`](https://github.com/tokenpak/tokenpak/blob/main/tests/companion/recall/test_reason_codes_and_risk_flags.py)
