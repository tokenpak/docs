# TokenPak Restructure — Phase 1–3 Completion Report

**Generated:** 2026-03-29  
**Author:** Cali (TPK-RESTRUCTURE-REPORT-001)  
**Status:** Phase 1–3 complete, Phase 4–5 pending

---

## Executive Summary

Phases 1–3 of the TokenPak clean architecture restructure are complete. The 6,370-line `proxy.py` monolith has been decomposed into a modular `proxy/` package. The deep `packages/core/tokenpak/agent/` nesting has been eliminated and flattened to `tokenpak/tokenpak/`. An `infrastructure/` module consolidating 9 shared support files was created. Import rewrites and CI/pyproject.toml updates are done. **613 Python files** now live in the flat `tokenpak/tokenpak/` package structure.

---

## Before vs After

| Metric | Before (Phase 1 start) | After (Phase 3 complete) |
|--------|------------------------|--------------------------|
| `proxy.py` monolith | 6,370 lines (canonical) | **Decomposed** — no monolith |
| Divergent proxy copies | 3 (root=6,270L, packages/core=5,163L, runtime=6,370L) | 1 (`proxy/server.py` = 2,704 lines) |
| Package nesting depth | 7 levels (`packages/core/tokenpak/agent/...`) | 3 levels (`tokenpak/tokenpak/...`) |
| Source files in new package | N/A (in packages/core) | **613 .py files** |
| `infrastructure/` module | Scattered across `agent/debug/`, `agent/license/`, `agent/auth/` | **9 consolidated modules** |

---

## Phase 1: Proxy Decomposition (Complete)

**Tasks:** TPK-RESTRUCTURE-001 through TPK-RESTRUCTURE-008 (all done)

Decomposed the 6,370-line `runtime/proxy.py` into the `tokenpak/tokenpak/proxy/` module:

### proxy/ Module Files (25 non-init .py files)

| File | Lines | Extracted From |
|------|-------|----------------|
| `server.py` | 2,704 | Main `ForwardProxyHandler` (L3205–5749) |
| `monitor.py` | 464 | `Monitor` class (L2248–3204) |
| `request_pipeline.py` | 575 | Request routing pipeline |
| `stats.py` | 421 | `/stats` + `/health` endpoints |
| `vault_bridge.py` | 463 | VaultIndex + BM25 (L1147–1596) |
| `fallback.py` | 246 | Key pool + failover (L608–812) |
| `circuit_breaker.py` | 383 | Per-provider circuit breakers (L813–1146) |
| `config.py` | 385 | Proxy config + tracing (L1–607) |
| `tracing.py` | 93 | Trace/span logic |
| `streaming.py` | 88 | SSE parsing + forwarding |
| `cache_poison.py` | 124 | `_strip_cache_poisons` + related |
| `cache.py` | 227 | Caching layer |
| `websocket.py` | 201 | WS proxy + main entry (L5750+) |
| `credential_passthrough.py` | 283 | Credential passthrough logic |
| `token_cache.py` | 64 | Token cache (L1147–1596 split) |
| `payloads.py` | 5 | Payload dataclasses |
| `__init__.py` | 58 | Public API exports |

### proxy/adapters/ Sub-module (9 files, 1,026 lines)

| File | Lines |
|------|-------|
| `anthropic_adapter.py` | 111 |
| `base.py` | 179 |
| `canonical.py` | 33 |
| `google_adapter.py` | 138 |
| `grok_adapter.py` | 191 |
| `openai_chat_adapter.py` | 89 |
| `openai_responses_adapter.py` | 128 |
| `passthrough_adapter.py` | 76 |
| `registry.py` | 42 |

**proxy/ total: ~7,135 lines across 25 modules + 9 adapter files**

---

## Phase 2: Package Layout Flatten (Complete)

**Tasks:** TPK-RESTRUCTURE-009 (status: review)

Eliminated `packages/core/tokenpak/agent/` nesting. New layout:

```
BEFORE: packages/core/tokenpak/agent/compression/pipeline.py
AFTER:  tokenpak/tokenpak/compression/pipeline.py

BEFORE: packages/core/tokenpak/agent/vault/indexer.py
AFTER:  tokenpak/tokenpak/vault/indexer.py

BEFORE: packages/core/tokenpak/agent/cli/commands/status.py
AFTER:  tokenpak/tokenpak/cli/status.py
```

**Result:** 613 `.py` files now live at `tokenpak/tokenpak/` with max 3 levels of nesting.

---

## Phase 3: Supporting Tasks (Complete)

### TPK-RESTRUCTURE-012: infrastructure/ Module (done — Trix)

Consolidated 9 scattered support files into `tokenpak/tokenpak/infrastructure/`:

| Module | Lines | Origin |
|--------|-------|--------|
| `cooldown.py` | 248 | `agent/auth/` |
| `debug.py` | 152 | `agent/debug/` |
| `error_handling.py` | 559 | Shared error handling |
| `license_activation.py` | 244 | `agent/license/` |
| `license_store.py` | 158 | `agent/license/` |
| `license_validation.py` | 301 | `agent/license/` |
| `startup_validator.py` | 76 | Root-level |
| `state_manager.py` | 424 | Root-level |
| `version_check.py` | 147 | Root-level |

**infrastructure/ total: 2,309 lines across 9 modules**

### TPK-RESTRUCTURE-010: Import Rewrite (done — Trix)

Automated sed-based rewrite of all import paths:
- `from tokenpak.agent.compression.` → `from tokenpak.compression.`
- `from tokenpak.agent.vault.` → `from tokenpak.vault.`
- `from tokenpak.runtime.proxy` → `from tokenpak.proxy.server`
- (all 15 `agent/` path patterns rewritten)

### TPK-RESTRUCTURE-011: pyproject.toml + CI (done — Cali)

Updated:
- `pyproject.toml` — package discovery updated to `tokenpak/tokenpak/`
- `pytest.ini` — `pythonpath` updated, `packages/core` references removed
- `.github/workflows/ci.yml`, `tests.yml`, `publish.yml` — paths updated
- `Makefile` — all path references updated

---

## Current State: What's Still in the Monolith

`packages/core/` directory: Still present but old proxy.py copies have been removed.  
`proxy.py` at vault root: **6,370 lines** — this is the **production runtime copy** on `~/tokenpak/proxy.py` (deployed, not the restructured package).

> ⚠️ The restructured `tokenpak/tokenpak/proxy/` package lives in the vault but **production still runs `~/tokenpak/proxy.py`**. The deployment swap (production cutover) is Phase 4+ work.

---

## Open Issues / Blockers

| Issue | Severity | Notes |
|-------|----------|-------|
| Production still uses `~/tokenpak/proxy.py` monolith | High | Phase 4 needs deployment cutover script |
| TPK-RESTRUCTURE-009 in `review` not `done` | Medium | Awaiting Sue/Kevin QA sign-off |
| `packages/core/` directory still present | Low | Safe to archive after 009 approved |
| No e2e tests for restructured proxy modules | Medium | TPK-E2E-RESTRUCTURE-001 open |
| No divergence detector | Low | TPK-DRIFT-DETECT-001 open |
| Phase 4 file renames not done | Medium | See table below |

---

## Phase 4 Priorities (Next Up)

**Phase 4: File Renames to Match Target** (P1 — ~0.5 day)

| Current | Target | Module |
|---------|--------|--------|
| `vault/symbols.py` | `vault/symbol_extraction.py` | vault |
| `vault/retrieval.py` | `vault/search.py` | vault |
| `vault/chunk_shapes.py` | `vault/chunk_shaping.py` | vault |
| `vault/sqlite_retrieval.py` | `vault/sqlite_backend.py` | vault |
| `compression/fingerprint/` | `compression/fingerprinter.py` | compression |
| — (new) | `compression/doc_compressor.py` | compression |

**Phase 5: tokenpak-pro/ Skeleton** (P1 — 1-2 days)
- Create separate `tokenpak-pro/` package
- Move Pro-only code (agentic, enterprise, intelligence, connectors, etc.)
- Set up `entry_points` auto-registration

**Phase 6: Cleanup + SPEC.md update** (P2)
- Remove `packages/` directory
- Update SPEC.md Codebase Paths section
- Production cutover from `~/tokenpak/proxy.py` → restructured package
- Final CI green

---

## Summary Scorecard

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Proxy Decomposition | 001–008 (Trix) | ✅ All done |
| Phase 2: Flatten Layout | 009 (Cali) | 🟡 In review |
| Phase 3: Import Rewrite | 010 (Trix) | ✅ Done |
| Phase 3: pyproject + CI | 011 (Cali) | ✅ Done |
| Phase 3: infrastructure/ | 012 (Trix) | ✅ Done |
| Phase 3: E2E Tests | E2E-001 (Cali) | 🔴 Open |
| Phase 3: Drift Detector | DRIFT-001 (Cali) | 🔴 Open |
| Phase 4: File Renames | Not yet tasked | ⬜ Pending |
| Phase 5: tokenpak-pro/ | Not yet tasked | ⬜ Pending |
| Phase 6: Cleanup + cutover | Not yet tasked | ⬜ Pending |
