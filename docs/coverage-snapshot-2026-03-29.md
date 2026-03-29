# Coverage Snapshot — 2026-03-29

## Summary

| Metric | Value |
|--------|-------|
| **Total coverage** | **12%** |
| Tests passing | 763 |
| Tests skipped | 20 |
| Total statements | 60,930 |
| Covered statements | ~7,505 |
| Test suite runtime | ~21s (default testpaths, non-slow/integration) |

## Progress

- **Previous baseline:** ~3% (quick/proxy/protocol tests only)
- **This snapshot:** 12% (full default testpaths: unit, proxy, protocol, adapters, dashboard, determinism, feature-wave4, integrations, quick)
- **Target:** 80%
- **Gap:** ~68 percentage points remaining

## Well-Covered Modules (≥80%)

| Module | Coverage |
|--------|----------|
| `agent/dashboard/session_filter.py` | 98% |
| `proxy/cache_poison.py` | 97% |
| `proxy/streaming.py` | 96% |
| `proxy/adapters/registry.py` | 96% |
| `agent/dashboard/export_csv.py` | 96% |
| `adapters/anthropic.py` | 94% |
| `proxy/adapters/grok_adapter.py` | 93% |
| `proxy/circuit_breaker.py` | 86% |
| `validator.py` | 77% |

## Top Gaps — 0% Coverage (by line count)

| Module | Lines | Priority |
|--------|-------|----------|
| `cli.py` | 4,052 | HIGH — largest uncovered file |
| `telemetry/server.py` | 539 | HIGH — telemetry server untested |
| `agent/proxy/server_async.py` | 529 | HIGH — async proxy server |
| `agent/cli/main.py` | 510 | HIGH — CLI entry point |
| `agent/cli/commands/doctor.py` | 465 | MEDIUM |
| `telemetry/segmentizer.py` | 383 | MEDIUM |
| `agent/cli/commands/budget.py` | 381 | MEDIUM |
| `telemetry/dashboard/dashboard.py` | 377 | MEDIUM |
| `telemetry/storage.py` | 347 | MEDIUM |
| `agent/proxy/providers/translator.py` | 332 | MEDIUM |
| `benchmark.py` | 297 | LOW |
| `agent/agentic/workflow.py` | 272 | MEDIUM |
| `precompute.py` | 265 | LOW |
| `intelligence/ab_optimizer.py` | 257 | MEDIUM |

## Entire Subsystems at 0%

- **`telemetry/`** — all modules (collector, cost, pipeline, storage, rollups, etc.)
- **`agent/cli/commands/`** — all CLI command modules
- **`validation/`** — all validation modules
- **`monitoring/`** — untested
- **`enterprise/`** — untested
- **`pro/`** — untested

## Path to 80%

To reach 80%, roughly 41,600 additional statements need coverage. The highest leverage areas:

1. **`cli.py`** (4,052 lines) — CLI smoke tests would yield the biggest single gain
2. **`telemetry/`** subsystem — collector, storage, pipeline, rollups (3,000+ lines total)
3. **`agent/cli/commands/`** — budget, workflow, dashboard, doctor (1,400+ lines)
4. **`validation/`** — request_validator, validator (350+ lines)
5. **`agent/proxy/server_async.py`** — async proxy (529 lines)

## Notes

- The xdist benchmark warning (benchmarks auto-disabled in parallel mode) is non-blocking.
- Ollama circuit-breaker warnings are expected in CI (upstream unreachable).
- Integration/live/slow/chaos/e2e/load tests excluded from this run — may add coverage if included.
