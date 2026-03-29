# README Audit — 2026-03-29

**Auditor:** Cali  
**Task:** TPK-README-AUDIT-001  
**File audited:** `~/vault/01_PROJECTS/tokenpak/README.md`  
**Scope:** Installation, CLI commands, API endpoints, config options, code examples

---

## ✅ Accurate sections

1. **Installation — `pip install tokenpak`**: Package is installable and present (`tokenpak 1.0.2` confirmed via `pip show tokenpak`).
2. **Python 3.10+ requirement**: `pyproject.toml` confirms `target-version = "py310"` and badge reflects 3.10–3.13.
3. **`tokenpak[server]` extra**: `pyproject.toml` has `[project.optional-dependencies] server = ["fastapi>=0.100", ...]` — exists.
4. **CLI command `tokenpak serve`**: Confirmed present in CLI (`--port`, `--workers`, `--shutdown-timeout` flags verified).
5. **CLI command `tokenpak demo`**: Confirmed present (`--list`, `--category`, `--recipe`, `--seed` flags).
6. **CLI command `tokenpak cost`**: Confirmed present (`--week`, `--month`, `--by-model`, `--export-csv` flags).
7. **CLI command `tokenpak status`**: Confirmed present and functional — returns proxy stats.
8. **`X-TokenPak-Bypass` header** (true/1/yes): Verified in `proxy.py` lines 4037–4038 — exact values `"true"`, `"1"`, `"yes"` handled; logs `compilation_mode=bypass`. ✅
9. **`TOKENPAK_PROFILE` env var** (`safe|balanced|aggressive|agentic`): Confirmed in `proxy.py` line 299–303. All four profiles listed match the code.
10. **Docker Compose port mapping 8766:8766**: Confirmed in `packages/core/docker-compose.yml`.
11. **`/health` endpoint exists**: Returns JSON with `status: ok`. ✅
12. **`/v1/messages` and `/v1/chat/completions` endpoints**: Both found in `proxy.py` `_POST_ONLY_PATHS`. ✅
13. **Notebooks exist** (`quickstart.ipynb`, `compression-strategies.ipynb`, `routing-fallback.ipynb`, `cost-tracking.ipynb`): All four confirmed in `examples/notebooks/`. ✅
14. **CONTRIBUTING.md, SECURITY.md, CHANGELOG.md at repo root**: All confirmed present.
15. **`packages/core/README.md` and `docs/QUICKSTART.md`**: Both files confirmed present.
16. **`docs/adapters/google.md`**: File exists at expected path. ✅
17. **Shell completion script `scripts/install-completions.sh`**: Confirmed present at that path.

---

## ⚠️ Stale/inaccurate sections

1. **Version shown in README badge and Changelog section says 1.0.3 (latest)**  
   - README lists `1.0.3 (2026-03-27)` as most recent in changelog summary  
   - `CHANGELOG.md` only contains entries up to `v1.0.2` (no `v1.0.1` entry either)  
   - `pyproject.toml` version is `1.0.2`, installed package reports `1.0.2`  
   - **Suggested fix:** Either add `v1.0.3` and `v1.0.1` entries to `CHANGELOG.md`, or update the README version list to stop at `1.0.2`.

2. **Health endpoint response example is inaccurate**  
   - README claims: `{"status": "ok", "version": "1.0.2"}`  
   - Actual response: No `version` field. Response contains `compilation_mode`, `vault_index`, `router`, `stats`, and many other fields — `version` is absent.  
   - **Suggested fix:** Remove `"version"` from the example, or add version to the `/health` endpoint response.

3. **Developer clone URL inconsistency**  
   - Dev section (line ~34): `git clone https://github.com/tokenpak/tokenpak.git` (org: `tokenpak`)  
   - All other links in README use `github.com/tokenpak/tokenpak`  
   - **Suggested fix:** Standardize to `github.com/tokenpak/tokenpak` throughout, or confirm the OSS org name.

4. **`python3 -m tokenpak version` reports `0.5.0` for CLI, `1.0.2` for package**  
   - README only references version `1.0.x` but the CLI self-reports as `TokenPak CLI: 0.5.0`  
   - This suggests the installed package (PyPI `1.0.2`) and the vault-local CLI version (`0.5.0`) are different builds  
   - **Suggested fix:** Clarify versioning; ensure CLI version string matches package version, or document the dual versioning.

5. **README version history is incomplete**  
   - Lists `v1.0.1 — Fixed missing requests dependency` but no such entry exists in CHANGELOG.md  
   - **Suggested fix:** Add the missing `v1.0.1` and `v1.0.3` entries to CHANGELOG.md, or remove them from the README summary.

---

## 🔴 Broken examples

1. **`tokenpak serve` vs `tokenpak start` — proxy "version" check**  
   - README presents `tokenpak serve --port 8766` as the 5-minute quickstart command  
   - When run and then followed by `tokenpak version`, proxy reports "not reachable (HTTP Error 404: Not Found)" even though proxy is running on 8766  
   - The `/health` endpoint returns 200, but the CLI `version` command hits a different path that returns 404 — suggests a CLI version-check URL mismatch internally  
   - **Impact:** Minor (proxy works); user may see confusing "not reachable" in `tokenpak version` output even when serving correctly.

2. **GitHub Actions badge URL (`tokenpak/tokenpak`) may not resolve publicly**  
   - Badge URL points to `github.com/tokenpak/tokenpak/actions` — if repo is private or not yet published, badge will show broken/error state to public readers  
   - **Suggested fix:** Confirm repo is public before OSS launch; placeholder badge OK in private dev but should be verified.

---

## Summary

| Category | Count |
|----------|-------|
| ✅ Accurate claims verified | 17 |
| ⚠️ Stale/inaccurate | 5 |
| 🔴 Broken examples | 2 |
| **Total checked** | **24** |

**Top priority fixes before OSS launch:**
1. Fix the `health` endpoint example (remove `version` field or add it to the response)
2. Resolve git clone URL inconsistency (`tokenpak` org (resolved))
3. Add missing CHANGELOG entries for `v1.0.1` and `v1.0.3`
4. Investigate CLI version string mismatch (`0.5.0` vs `1.0.2`)
