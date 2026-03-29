# VaultIndex Cold Load Performance Analysis
**Date:** 2026-03-29  
**Author:** Trix  
**Task:** TPK-VAULT-INDEX-PERF-001  
**Baseline:** 69.5s cold load (9,370 blocks, 228MB)

---

## Profiling Results

Run: `cProfile` on `VaultIndex.maybe_reload()` with warm OS page cache.

| Function | Calls | Total time | Notes |
|---|---|---|---|
| `pathlib.read_text` (file reads) | 9,371 | 6.47s | One open per block |
| `re.findall` (BM25 tokenize) | 9,289 | 6.37s | Regex tokenization |
| `dict.get` (TF counting) | 27,175,360 | 5.89s | Per-token BM25 accounting |
| `set.add` (inverted index) | 3,043,388 | 1.46s | Building inverted index |
| `pathlib.stat` (mtime check) | 28,112 | 0.96s | Exists + preload scoring |
| Thread lock acquisition | 135 | 7.52s | Background threads (Ollama health check) |

**Total (warm OS cache):** ~32-35s  
**Total (cold OS cache):** ~69.5s — additional ~35s is disk I/O latency for 9,371 individual file opens

## Root Cause

### Primary: 9,371 individual file reads
Each block is stored as a separate `.txt` file. Reading them one-by-one:
- 9,371 `Path.open()` syscalls + `read()` 
- On cold disk: ~4-5ms per file × 9,371 = ~40-45s
- On warm OS cache: ~0.7ms per file × 9,371 = ~6.5s

### Secondary: Python BM25 dict overhead
Building TF dicts and inverted index requires:
- 27M `dict.get()` calls (per-token frequency counting)
- 3M `set.add()` calls (inverted index)
- ~12s pure CPU on warm load

### Why BM25 cache (pickle) didn't help
Implemented a `.bm25_cache.pkl` file (53MB). Cold load: 32.9s. Cache load: 31.4s.  
**No speedup** — pickle deserialization of large nested Python dicts is ~as slow as rebuilding them. Python must reconstruct every dict/set object individually.

---

## Recommended Approaches (Ranked by Impact)

### 1. Parallel file reads — `ThreadPoolExecutor` (estimated: 60-70% reduction) ⭐ Quick win

Replace serial `content_file.read_text()` loop with parallel reads:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _read_block(bid_bdata_dir):
    bid, bdata, blocks_dir = bid_bdata_dir
    content_file = blocks_dir / f"{bid}.txt"
    if not content_file.exists():
        return None
    try:
        content = content_file.read_text(errors="replace")
        mtime = content_file.stat().st_mtime
        return (bid, bdata, content, mtime)
    except OSError:
        return None

with ThreadPoolExecutor(max_workers=16) as pool:
    results = list(pool.map(_read_block, [(bid, bdata, blocks_dir) for bid, bdata in items]))
```

**Expected impact:**
- Cold start: ~69.5s → ~15-20s (16 threads, disk I/O parallelized)
- Warm start: ~32s → ~10s (I/O already fast, overhead from BM25 still ~12s)

### 2. Consolidated block store — single `blocks.tar` or SQLite (estimated: 80%+ reduction)

Instead of 9,371 individual files, store all block content in:
- A single `blocks.db` SQLite file (random access by block_id)
- Or `blocks.msgpack` (sequential read, deserialize all at once)

Single-file read of 228MB is ~2-3s vs 9,371 individual opens at ~40-45s cold.
Also reduces inode overhead on the filesystem.

**Tradeoff:** Requires index rebuilder changes (rebuild-vault-index.sh).

### 3. NumPy/scipy sparse matrix BM25 (estimated: 70-80% cache load reduction)

Replace Python dicts with numpy arrays for TF/IDF storage:
- Vocabulary → integer IDs (array index)
- TF matrix: `scipy.sparse.csr_matrix` (9370 docs × vocab_size)
- BM25 scores: precomputed as float32 array

Numpy `np.load()` of mmap'd arrays: ~0.5s for 50MB. No object reconstruction.

**Tradeoff:** Requires scipy dep + significant refactor of `search()`.

### 4. Background async load (estimated: eliminates startup penalty)

Start serving immediately on proxy launch; load VaultIndex in a background thread.
Vault injection degrades gracefully (inject nothing) until index is ready.

```python
# In proxy startup:
threading.Thread(target=VAULT_INDEX.maybe_reload, daemon=True).start()
# Index available in ~70s; requests before that get no vault injection
```

**Tradeoff:** First ~70s of requests get no context injection. Fine for restart scenarios.

---

## Implemented

Added `_try_load_bm25_cache` / `_save_bm25_cache` to `VaultIndex` in `~/tokenpak/proxy.py`.

**Status:** Cache saves (53MB pickle) but loads at same speed (~31s) as rebuild. No regression, but no speedup. Framework is in place for a faster serialization format (approach #3 above).

**Recommendation:** Approach #1 (parallel reads) is the highest-impact, lowest-risk quick win. Implement in a follow-up task.

---

## Data

```json
{
  "blocks": 9370,
  "total_size_mb": 228,
  "index_json_mb": 7.2,
  "avg_block_size_kb": 24.9,
  "largest_block_bytes": 3138653,
  "cold_load_ms": 69536,
  "warm_load_ms": 32900,
  "bm25_cache_size_mb": 53,
  "cache_load_ms": 31400
}
```
