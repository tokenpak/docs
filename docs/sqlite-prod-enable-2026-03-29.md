# SQLite Block Store Production Enable — Benchmark Report

**Date:** 2026-03-29
**Agent:** Cali
**Task:** TPK-SQLITE-PROD-ENABLE-001

## Migration Results

- **Source:** `~/vault/.tokenpak/blocks/` — 11,770 block files
- **Destination:** `~/vault/.tokenpak/blocks.db`
- **Migration time:** 129,752ms (~2.16 min)
- **DB size:** 210.8MB
- **Blocks migrated:** 11,770 (skipped: 0)

## Benchmark Results

| Load method | Time | Blocks | Notes |
|-------------|------|--------|-------|
| Cold file-based (no BM25 cache) | 23.668s | 9,370 | `_load()` with no .bm25_cache.pkl |
| File-based (BM25 cache hit) | 7.677s | 9,370 | Normal warm path |
| **SQLite (`TOKENPAK_USE_SQLITE_BLOCKS=1`)** | **149.619s** | **11,770** | Full content + BM25 rebuild in-memory |

## ⚠️ Escalation Required

SQLite load is **~6.3x SLOWER** than cold file-based load, and **~20x SLOWER** than the cached path.

**Root cause analysis:**
1. SQLite path loads all 11,770 block contents into memory (201MB) AND rebuilds full BM25 structures from scratch — no BM25 cache utilized
2. File-based path with BM25 cache only needs to deserialize a 53MB pickle (mostly precomputed BM25 state + 9,370 block metadata stubs)
3. SQLite has 25% more blocks (11,770 vs 9,370) — index.json may be stale/subset

**Why the BM25 cache path is faster:**
- `_load_from_sqlite()` rebuilds BM25 from scratch (tokenizes all 11,770 full block contents)
- The BM25 pickle cache path skips full content loading — just restores precomputed df/tfs/inverted index
- SQLite has 2,400 extra blocks not in index.json (likely added since last `rebuild-vault-index.sh`)

## Decision: DO NOT Enable SQLite in Production

Per task criteria: "Escalate if blocks.db doesn't improve load time (within 2x of file-based) — alert Sue"

SQLite is 6x worse, not 2x better. **Do not add `TOKENPAK_USE_SQLITE_BLOCKS=1` to `.env`.**

## Recommendation for Sue

The SQLite implementation needs to also persist the BM25 state (like `.bm25_cache.pkl` does) so that 
subsequent loads don't need to rebuild BM25 from scratch. Options:

1. **Store precomputed BM25 in SQLite** — add a `bm25_cache` table alongside `blocks` table
2. **Hybrid approach** — use SQLite for content storage but still save/load BM25 pickle cache
3. **Keep current BM25 cache path** — it's already fast (7.7s warm, 23.7s cold), SQLite adds no value without BM25 persistence

The `blocks.db` file was created and is valid. The migration script works correctly.
Implementation needs architectural adjustment before production enablement.
