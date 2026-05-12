# Context Package `ordering_hints` examples

`OrderingHints` is the optional, additive cache-aware ordering field on a Context Package. It lets a producer state preferences about block ordering — stable content first, output requirements last, anchor snippets in a known position — so a downstream consumer (or the Pro Phase 3 Context Package builder) can preserve cache hits and produce a deterministic byte layout.

This page shows the field in three forms:

1. The wire shape.
2. The Python dataclass that emits it.
3. Concrete example manifests for the common use patterns.

The full TIP context-package schema is published at [`https://docs.tokenpak.ai/schemas/tip/context-package-v1.json`](https://docs.tokenpak.ai/schemas/tip/context-package-v1.json).

---

## The byte-shape invariant

`ordering_hints` is additive within TIP-1.x. The receiver-side contract is:

!!! note "Ignorant receivers produce a valid package"
    A receiver that does not recognise `ordering_hints` ignores the field and produces a **valid** (just unoptimised) package. The receiver's behaviour is identical to the pre-addendum behaviour.

`ContextPackage.to_dict()` enforces this from the producer side too: when the dataclass is constructed without ordering hints (`ordering_hints=None`), the field is **omitted entirely** from the serialized payload. Old receivers see byte-identical output to the pre-addendum shape. New receivers see the field when (and only when) it was set.

This is the invariant to protect when tooling around the package — diff tools, golden fixtures, byte-stable transports should all behave the same way on an old package and a new package whose producer did not set `ordering_hints`.

---

## Fields

```python
@dataclass(frozen=True)
class OrderingHints:
    stable_first: bool = True
    task_delta_after_stable_context: bool = True
    output_requirements_near_end: bool = True
    cache_sensitive_blocks: tuple[str, ...] = ()
    anchor_block_position: AnchorBlockPosition = AnchorBlockPosition.END
```

| Field | Default | Meaning |
|---|---|---|
| `stable_first` | `True` | Place stable / reusable Pak content before volatile task delta. Cache-aware. |
| `task_delta_after_stable_context` | `True` | Mandatory and primary Paks appear after stable / reusable Paks (consistent with `stable_first`). |
| `output_requirements_near_end` | `True` | Output-shape instructions immediately precede the cursor / model. |
| `cache_sensitive_blocks` | `()` | Block IDs whose ordering must not change once assembled. |
| `anchor_block_position` | `END` | Where hydrated anchor snippets sit. Closed enum: `END`, `INLINE`, `OMIT`. |

`anchor_block_position` is a closed enum within TIP-1.x — receivers reading an unknown value raise `ValueError`. The field set itself is additive (new optional fields may be added in a future TIP-1.x minor), but the enum admits no surprise values.

---

## Example 1 — All defaults (cache-aware, anchors at end)

The most common manifest. Stable / reusable Paks first, task delta after, output requirements near the end, anchor snippets appended after the main Pak content.

```json
{
  "package_id": "ctx_2026-05-12_a1b2c3",
  "scope": {
    "user_scope": "local_user",
    "project_scope": "tokenpak",
    "target_platform": "anthropic",
    "target_task": "implement"
  },
  "recall_query": "explain the OSS recall reason / risk surface",
  "context_level": "handoff_pak",
  "included_pak_ids": [
    "vault:auth-pattern#a1b2c3",
    "vault:recall-storage#d4e5f6",
    "vault:risk-flags-catalogue#7g8h9i"
  ],
  "hydrated_anchor_ids": [
    "anchor:store.py:548-732"
  ],
  "coverage": {
    "state": "complete",
    "required_paks": 3,
    "included_paks": 3,
    "hydrated_anchors": 1,
    "missing_context": [],
    "confidence": "high"
  },
  "policy": {
    "cross_project_blocked": false,
    "sensitive_blocked": false,
    "hydration_budget_exceeded": false,
    "blocked_pak_ids": [],
    "blocked_anchor_ids": [],
    "reasons": []
  },
  "generated_at": "2026-05-12T17:14:09Z",
  "memory_horizon": "recent",
  "privacy_class": "local_only",
  "ordering_hints": {
    "stable_first": true,
    "task_delta_after_stable_context": true,
    "output_requirements_near_end": true,
    "cache_sensitive_blocks": [],
    "anchor_block_position": "end"
  }
}
```

This is the recommended starting point for any package that wants to stay cache-friendly.

---

## Example 2 — Anchors interleaved with their referencing block

For tasks where anchor snippets are tightly coupled to the surrounding Pak narrative (e.g. code review with inline references), set `anchor_block_position` to `inline`. The producer is asserting that ordering anchors near their citation point matters more than the cache benefit of keeping all anchors at the end.

```json
{
  "...": "(other fields as in Example 1)",
  "ordering_hints": {
    "stable_first": true,
    "task_delta_after_stable_context": true,
    "output_requirements_near_end": true,
    "cache_sensitive_blocks": [],
    "anchor_block_position": "inline"
  }
}
```

This is a cache-cost tradeoff: anchor blocks inserted mid-package will shift the byte offsets of every following block. Old receivers (which ignore `ordering_hints`) still see a valid package — just one that may benefit less from cache reuse.

---

## Example 3 — Drop anchors entirely (budget-constrained)

For a tight token budget, set `anchor_block_position` to `omit`. The Pak content is included; the hydrated anchor snippets are not. The Pak `summary` field still carries the headline.

```json
{
  "...": "(other fields as in Example 1)",
  "hydrated_anchor_ids": [],
  "coverage": {
    "state": "partial",
    "required_paks": 3,
    "included_paks": 3,
    "hydrated_anchors": 0,
    "missing_context": ["anchor:store.py:548-732 omitted by ordering_hints"],
    "confidence": "medium"
  },
  "ordering_hints": {
    "stable_first": true,
    "task_delta_after_stable_context": true,
    "output_requirements_near_end": true,
    "cache_sensitive_blocks": [],
    "anchor_block_position": "omit"
  }
}
```

When `anchor_block_position = omit`, the package's `coverage` state typically downgrades from `complete` to `partial` so the receiver understands the omission was a producer choice, not a recall miss.

---

## Example 4 — Cache-sensitive block pinning

`cache_sensitive_blocks` names blocks whose ordering relative to their neighbours must not change once the package is assembled. A typical case: a long stable preamble (governance pin, project README, glossary excerpt) that you want to retain across many subsequent task deltas so the upstream provider's cache hits the same prefix on every call.

```json
{
  "...": "(other fields as in Example 1)",
  "included_pak_ids": [
    "vault:project-readme#0aa00",
    "vault:governance-pin#0bb01",
    "vault:glossary-multipak#0cc02",
    "vault:current-task-spec#7g8h9i"
  ],
  "ordering_hints": {
    "stable_first": true,
    "task_delta_after_stable_context": true,
    "output_requirements_near_end": true,
    "cache_sensitive_blocks": [
      "vault:project-readme#0aa00",
      "vault:governance-pin#0bb01",
      "vault:glossary-multipak#0cc02"
    ],
    "anchor_block_position": "end"
  }
}
```

A consumer that respects `cache_sensitive_blocks` will not re-order or partially elide those block IDs even under budget pressure — it will drop the volatile task delta first.

---

## Example 5 — Producer chose **not** to set ordering hints

This package was built by a producer that did not write `ordering_hints` (legacy producer, or a producer that has opted out). The serialized payload **omits the field entirely**:

```json
{
  "package_id": "ctx_2026-05-12_legacy",
  "scope": { "...": "..." },
  "recall_query": "...",
  "context_level": "handoff_pak",
  "included_pak_ids": [ "..." ],
  "hydrated_anchor_ids": [ "..." ],
  "coverage": { "...": "..." },
  "policy": { "...": "..." },
  "generated_at": "2026-05-12T17:14:09Z",
  "memory_horizon": "recent",
  "privacy_class": "local_only"
}
```

A new receiver that does recognise the field treats the absence as "no preference": it uses sensible defaults (`stable_first=true`, `anchor_block_position=end`) but is not allowed to fabricate the field in the package. The byte shape on the wire — and any golden fixtures — stays pre-addendum.

---

## Producer-side Python — emitting a package with hints

```python
from tokenpak.tip.context_package import (
    AnchorBlockPosition,
    ContextLevel,
    ContextPackage,
    ContextScope,
    CoverageConfidence,
    CoverageReport,
    CoverageState,
    OrderingHints,
    PolicyDecision,
)

pkg = ContextPackage(
    package_id="ctx_2026-05-12_a1b2c3",
    scope=ContextScope(
        project_scope="tokenpak",
        target_platform="anthropic",
        target_task="implement",
    ),
    recall_query="explain the OSS recall reason / risk surface",
    context_level=ContextLevel.HANDOFF_PAK,
    included_pak_ids=(
        "vault:auth-pattern#a1b2c3",
        "vault:recall-storage#d4e5f6",
        "vault:risk-flags-catalogue#7g8h9i",
    ),
    hydrated_anchor_ids=("anchor:store.py:548-732",),
    coverage=CoverageReport(
        state=CoverageState.COMPLETE,
        required_paks=3,
        included_paks=3,
        hydrated_anchors=1,
        confidence=CoverageConfidence.HIGH,
    ),
    policy=PolicyDecision(),
    generated_at="2026-05-12T17:14:09Z",
    ordering_hints=OrderingHints(
        cache_sensitive_blocks=(
            "vault:project-readme#0aa00",
            "vault:governance-pin#0bb01",
        ),
        anchor_block_position=AnchorBlockPosition.END,
    ),
)

wire = pkg.to_dict()
assert "ordering_hints" in wire
```

Omitting the field at construction time produces a payload that is byte-identical to the pre-addendum shape:

```python
pkg_legacy = ContextPackage(
    # ... same fields as above, but no ordering_hints ...
    ordering_hints=None,
)

wire_legacy = pkg_legacy.to_dict()
assert "ordering_hints" not in wire_legacy
```

This is the byte-shape invariant in code form.

---

## Receiver-side Python — reading hints back

`OrderingHints.from_wire` parses a wire-form mapping back into the dataclass. Unknown `anchor_block_position` values raise `ValueError`; new optional fields are tolerated.

```python
from tokenpak.tip.context_package import ContextPackage

pkg = ContextPackage.from_dict(wire)
if pkg.ordering_hints is not None:
    hints = pkg.ordering_hints
    if hints.anchor_block_position is AnchorBlockPosition.OMIT:
        ...
    if hints.cache_sensitive_blocks:
        ...
```

If `ordering_hints` is absent from the wire payload, `pkg.ordering_hints` is `None`. Receivers that depend on hints should default sensibly in that case (don't synthesize the field; treat absence as "use my own defaults").

---

## Related

- TIP context-package schema: [`context-package-v1.json`](https://docs.tokenpak.ai/schemas/tip/context-package-v1.json)
- [Pak Reason Codes](reason-codes.md) — `cache_ordering_candidate` is the reason code that motivates entries in `cache_sensitive_blocks`.
- [Pak Risk Flags](risk-flags.md) — `cache_sensitive_ordering` is the corresponding `info`-severity flag for a package.
- [Deterministic Recall Pak selection](selection-explanation.md) — `cache_ordering_candidate` is one of the signals an OSS selector can pin into `cache_sensitive_blocks`.
