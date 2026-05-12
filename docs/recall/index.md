# Recall — Paks, reason codes, risk flags, and Context Packages

TokenPak's recall surface stores the **memory** the AI session brings to the table: Paks (units of recall-able context), the reasons each Pak is or isn't included in a package, and the risk flags that should travel with it.

The OSS recall layer is a transparent data plane:

- It **persists** Paks, FTS shadows, reason codes, and risk flags.
- It **exposes** them via the `tokenpak.companion.recall` Python API.
- It **inspects** and **exports** them via the `tokenpak pak` CLI.
- It does **not** rank, score, or enforce. The Pro Phase 3 Context Package builder is the enforcement surface.

The page set below documents the OSS surface end-to-end.

---

## Pages

| Page | What it covers |
|---|---|
| [Pak Reason Codes](reason-codes.md) | The 28-code catalogue + per-category guidance for why a Pak is included or excluded. |
| [Pak Risk Flags](risk-flags.md) | The 13-flag catalogue + severity guidance + the OSS-does-not-refuse-on-`block` invariant. |
| [Recall store API](recall-store-api.md) | Read / write surface for `pak_reason_codes` and `pak_risk_flags` — round-trip, idempotency, FK cascade, validation. |
| [`tokenpak pak inspect` semantics](inspect-and-explain.md) | What `inspect` and `status` surface today, and what they surface as reason / risk rows populate. |
| [Deterministic Recall Pak selection](selection-explanation.md) | Narrative + pseudo-code showing how to pick Paks deterministically from OSS-visible signals. |
| [Context Package `ordering_hints` examples](ordering-hints-examples.md) | Sample manifests demonstrating the cache-aware ordering field — byte-shape invariant explained. |

---

## OSS vs Pro at a glance

| Surface | OSS | Pro Phase 3 |
|---|---|---|
| `pak_reason_codes` and `pak_risk_flags` storage | ✅ persist + expose | inherits the same storage |
| FTS5 search over Pak `title` + `summary` | ✅ via `paks_fts` MATCH | inherits |
| `tokenpak pak inspect` / `status` | ✅ Vault Paks | full Pak set |
| Reason-code scoring / ranking | ❌ — observability only | ✅ tuned scorer |
| `severity = block` enforcement | ❌ — data tag only | ✅ refuses to assemble |
| `ordering_hints` honoured during assembly | byte-stable pass-through | ✅ reorders accordingly |
| `tokenpak pak plan` / `assemble` / `validate` verbs | ❌ — not in OSS | ✅ daemon-served |

The recall **data** is the same on both sides. Only the consumption layer differs.

---

## Registry schemas

The closed catalogues are machine-readable JSON Schema documents on the public registry:

- [`pak-reason-codes-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-reason-codes-v1.json)
- [`pak-risk-flags-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-risk-flags-v1.json)
- [`context-package-v1.json`](https://docs.tokenpak.ai/schemas/tip/context-package-v1.json)
- [`pak-v1.json`](https://docs.tokenpak.ai/schemas/tip/pak-v1.json)

Pro-only extensions live in sibling `*.pro.json` overlays and must not be required by OSS receivers.
