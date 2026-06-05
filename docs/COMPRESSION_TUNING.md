---
title: "TokenPak Compression Tuning Guide"
subtitle: "Optimize token savings vs latency tradeoffs for your use case"
author: TokenPak
date: 2026-03-25
tags: [tokenpak, compression, tuning, performance]
---

# TokenPak Compression Tuning Guide

This guide explains **how to tune TokenPak's compression engine** to maximize token savings while minimizing latency impact for your specific workload.

## Overview: Why Compression Matters

LLM API costs scale with token count. TokenPak's compression pipeline intercepts requests and re-expresses semantically equivalent content with fewer tokens, with the magnitude of the reduction depending on your data.

> **Note on numbers:** This guide intentionally describes savings and latency in qualitative terms. TokenPak does not publish specific latency, savings, or cache-hit figures until they are backed by a validated, frozen-fixture benchmark run. Receipt-backed figures will be added once TokenPak's benchmark suite produces a validated run. In the meantime, **measure savings and latency on your own workload** — see [Monitoring](#monitoring) and run `tokenpak savings` / `tokenpak stats`.

### The Tradeoff

Compression trades a small amount of added latency for a reduction in token count. The right balance depends on your workload: latency-sensitive, real-time paths favor lighter pipelines, while batch and offline work can afford more aggressive compression for larger token reductions.

| Strategy | Added Latency | Token Savings | Best For |
|----------|---------------|---------------|----------|
| **Dedup** | Minimal | Small (on repeated context) | Iterative workflows, session context |
| **Segmentation** | Low | Small (metadata, structure) | Code review, doc analysis |
| **Alias compression** | Moderate | Moderate (long repeated names) | Large schemas, entity lists |
| **Instruction table** | Higher | Moderate (cookbook patterns) | Repetitive tasks, templates |
| **Semantic caching** (off) | N/A | Larger (on prompt cache hit) | Same prompts, different inputs |

**Default (all enabled):** low added latency for a modest token reduction. Acceptable for most workloads.

---

## Compression Strategies: How to Use Each

### Strategy 1: Dedup (Fast, Safe)

**What it does:** Removes duplicate message turns from conversation history.

**When it helps:**
- Iterative debugging (code repeatedly pasted)
- Multi-turn conversations where context is re-injected
- Workflow loops where the same block appears multiple times

**Real example:**

```
Message 1: "Here's the current auth schema:\n<200 lines JSON>"
Message 2: "Review line 42."
Message 3: [Assistant response]
Message 4: "Here's the current auth schema:\n<200 lines JSON>"  ← DEDUP removes this
Message 5: "Now add refresh tokens."
```

**Savings:** Small token reduction, scaling with how often context repeats.

**Configuration (in proxy config):**

```python
# tokenpak/proxy.py
pipeline = CompressionPipeline(
    enable_dedup=True,           # ← enable/disable
    enable_segmentation=True,
    enable_alias=True,
    enable_directives=True,
)
```

**When to disable:** Single-turn requests (queries, completions). No benefit, adds latency.

---

### Strategy 2: Segmentation (Safe, Structural)

**What it does:** Classifies message content into typed blocks (code, markdown, JSON, tool results, etc.) and applies targeted compression to each type.

**Strategies per segment type:**

| Segment Type | What Gets Compressed | Relative Savings | Risk |
|---|---|---|---|
| **Code** | Signature extraction, docstring keep | Higher | Low (retains logic) |
| **Markdown** | Keep headers, strip body text | Moderate | Medium (loses details) |
| **JSON** | Schema + sample data (strip repetitive rows) | Higher | Medium (loses volume) |
| **Tool results** | Truncation (keep first N lines) | Lower | Low (summaries) |
| **Text/prose** | Token filtering by importance | Moderate | High (selective) |

**Real example — code compression:**

```python
# Before
def calculate_total(items):
    """Calculate the sum of item values."""
    result = 0
    for item in items:
        result += item['price']
    return result

# After (signature only)
def calculate_total(items): ...
    """Calculate the sum of item values."""
```

**Configuration (in `proxy.py`):**

```python
pipeline = CompressionPipeline(
    enable_segmentation=True,    # ← enable/disable
    enable_dedup=True,
    enable_alias=True,
    enable_directives=True,
)

# Optionally provide a recipe (directives)
# See recipes/oss/*.yaml for examples
```

**When to disable:** If you need full code bodies preserved (not just signatures). Disabling trims a little added latency but gives up the compression segmentation would otherwise provide.

---

### Strategy 3: Alias Compression (Moderate)

**What it does:** Detects long repeated names/entities (variable names, long strings, UUIDs) and replaces them with short aliases.

**Real example:**

```
Before:
"The ManagerInterface.process_authentication_token() method..."
"Then ManagerInterface.process_authentication_token() handles..."
"Finally ManagerInterface.process_authentication_token() returns..."

After:
"The A1() method..."
"Then A1() handles..."
"Finally A1() returns..."

Mapping: A1 → ManagerInterface.process_authentication_token
```

**When it helps:**
- Long class/function names repeated 3+ times
- Domain-specific acronyms or entity names
- Code with verbose variable names

**Savings:** Moderate token reduction, scaling with repetition and name length.

**Configuration:**

```python
pipeline = CompressionPipeline(
    enable_alias=True,              # ← enable/disable
    alias_min_occurrences=3,        # minimum times to alias
    alias_min_length=20,            # minimum name length to alias
    enable_dedup=True,
    enable_segmentation=True,
)
```

**Tuning parameters:**
- `alias_min_occurrences=2` → more aggressive, catch 2+ repeats
- `alias_min_occurrences=5` → conservative, only high-frequency names
- `alias_min_length=15` → catch shorter names
- `alias_min_length=30` → only very long names

**When to disable:** If output is sent to users (aliases make it unreadable). Safe to disable; minimal latency impact.

---

### Strategy 4: Instruction Table (Advanced)

**What it does:** Uses a persistent table of common instructions and replaces repetitive task descriptions with references.

**Real example:**

```
Before:
"You are a code reviewer. Your job is to find bugs, suggest improvements, 
enforce style consistency, and suggest refactoring opportunities..."

After:
"Apply instruction [CODE-REVIEW-V2]"

Lookup table maps [CODE-REVIEW-V2] → full instruction text
```

**When it helps:**
- Batch processing (same role repeated 10+ times)
- Service agents (standard prompts)
- Workflows with template instructions

**Savings:** Moderate token reduction, scaling with instruction repetition.

**Configuration:**

```python
pipeline = CompressionPipeline(
    enable_instruction_table=True,                   # ← enable/disable
    instruction_table_path="path/to/instruction.db", # optional custom table
    context_budget_tight=True,                       # aggressive mode
    enable_dedup=True,
    enable_segmentation=True,
    enable_alias=True,
)
```

**How to add instructions:**

```python
# In your code:
from tokenpak.agent.compression.instruction_table import InstructionTable

table = InstructionTable(path="instruction.db")
table.add_instruction(
    id="CODE-REVIEW-V2",
    text="You are a code reviewer...",
)
```

**When to disable:** One-shot requests, unique prompts. Overhead > savings for low-repetition tasks.

---

### Strategy 5: Semantic Caching (Native to Claude API)

**What it does:** Reuses cached prompt prefixes when subsequent requests have similar context.

**How it works:**
- First request with context → stored in Claude's prompt cache (the API applies a default cache TTL)
- Identical or very similar context → reuses cached tokens at a reduced per-token cost on the cached prefix

**Real example:**

```
Request 1: "Here's the codebase:\n<large context>" → cache creation tokens written
Request 2: "Same codebase, different question" → cache read tokens (reduced cost on the cached prefix)

Effect: the repeated prefix is billed at the lower cache-read rate instead of full input cost.
```

**Savings:** Potentially large, but only on the repeated prefix when the cache is hit. Measure on your own traffic, since cache-hit rates depend heavily on how often prompts repeat.

**How to enable (in your client code):**

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a code reviewer. [... static system prompt ...]",
            "cache_control": {"type": "ephemeral"}  # ← enable caching
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here's the full codebase:\n" + large_code,
                    "cache_control": {"type": "ephemeral"}  # ← cache this too
                }
            ]
        }
    ]
)

# Subsequent requests with same codebase will hit the cache
```

**When to use:**
- System prompts (static, reused on every request)
- Large context blocks (code, docs, schemas) used in multiple requests
- Batch workflows where the same context applies to different questions

**When NOT to use:**
- One-off requests
- Context that changes every turn

---

## Performance Characteristics: Latency vs Savings

> **Benchmark figures pending.** Validated latency and savings numbers will be published once TokenPak's benchmark suite produces a receipt-backed, frozen-fixture run. Until then, treat the relative ordering below as guidance and **measure on your own workload** with `tokenpak savings` / `tokenpak stats` and the [Monitoring](#monitoring) snippet.

### Relative cost of each stage

The stages differ in how much latency they add and how much token reduction they typically deliver. Ordered from cheapest/lightest to most expensive:

| Stage | Added Latency | Token Savings | When it's worth it |
|---|---|---|---|
| **Dedup** | Minimal | Small | Almost always — very cheap, helps whenever context repeats |
| **Segmentation** | Low | Small | Usually — modest cost, broadly applicable |
| **Alias** | Moderate | Moderate | Worth it for code-heavy / entity-heavy workloads |
| **Instruction table** | Higher | Moderate | Worth it for batch / service work with repeated prompts |

**Analysis:**
- **Dedup:** lowest overhead of any stage; the savings are small but the cost is so low it is almost always worth enabling.
- **Segmentation:** low overhead, small savings; usually worth keeping on.
- **Alias:** moderate overhead with a moderate token reduction — most valuable on code-heavy workloads with long repeated names.
- **Instruction table:** the highest per-request overhead, but a moderate reduction on batch/service work where the same instructions repeat many times.

---

## Configuration: Copy-Paste Examples

### Example 1: Lightweight (Low Latency)

Use this for real-time chat, quick queries.

```python
# In proxy.py
pipeline = CompressionPipeline(
    enable_dedup=True,
    enable_segmentation=False,
    enable_alias=False,
    enable_instruction_table=False,
    enable_directives=False,
)
```

**Tradeoff:** Minimal added latency for a small token reduction.

---

### Example 2: Balanced (Default)

Use this for general workloads (development, analysis).

```python
# In proxy.py
pipeline = CompressionPipeline(
    enable_dedup=True,
    enable_segmentation=True,
    enable_alias=True,
    enable_instruction_table=False,
    enable_directives=True,
)
```

**Tradeoff:** Low added latency for a modest token reduction.

---

### Example 3: Aggressive (High Savings)

Use this for batch work, background jobs, offline analysis.

```python
# In proxy.py
pipeline = CompressionPipeline(
    enable_dedup=True,
    enable_segmentation=True,
    enable_alias=True,
    enable_instruction_table=True,
    enable_directives=True,
    context_budget_tight=True,
    alias_min_occurrences=2,      # catch more aliases
    alias_min_length=15,           # shorter names too
)
```

**Tradeoff:** Higher added latency for a larger token reduction.

---

### Example 4: Code Review Specialized

Optimized for code review tasks.

```python
# In proxy.py
pipeline = CompressionPipeline(
    enable_dedup=True,
    enable_segmentation=True,
    enable_alias=True,
    enable_instruction_table=True,
    enable_directives=True,
)

# Add custom hook for code-specific compression
def code_priority_hook(messages):
    """Keep code segments, compress narrative text."""
    for msg in messages:
        # Custom logic here
        pass
    return messages

pipeline.add_hook(code_priority_hook)
```

**Tradeoff:** Moderate added latency for a larger token reduction on code.

---

## Tuning Checklist

When you want to optimize compression for YOUR workload:

- [ ] **Profile your requests:** What's the typical size? Code? Text? JSON?
- [ ] **Set a baseline:** Run a week with `enable_all=True`, measure token savings.
- [ ] **Identify bottlenecks:** Which compression stage gives the most savings? (Use `PipelineResult.stages_run`)
- [ ] **Disable low-ROI stages:** If a stage (e.g. alias compression) adds noticeable latency for negligible savings on your data, disable it.
- [ ] **Batch profile:** Test on 100+ requests to get real averages (single-request measurements are noisy).
- [ ] **Test in production:** A/B test config changes on real workloads, measure cost + latency.

### Monitoring

```python
# After pipeline.run(), inspect:
result = pipeline.run(messages)

print(f"Tokens saved: {result.tokens_saved} ({result.savings_pct}%)")
print(f"Latency: {result.duration_ms}ms")
print(f"Stages run: {', '.join(result.stages_run)}")
```

---

## Common Tuning Questions

### Q: "Compression makes responses slightly different. Is this safe?"

**A:** TokenPak compression is **semantic-preserving**. The meaning of the request/response is identical; only formatting and redundancy are removed. Safe for production.

### Q: "Can I compress the response too?"

**A:** TokenPak currently compresses **requests only** (to LLM). Response compression would require client-side modifications. Future feature.

### Q: "How much should I save?"

**A:** It depends on your workload — there is no single number, and you should measure on your own traffic with `tokenpak savings` / `tokenpak stats`. As a rough ordering of where compression helps most to least:
- Code-heavy (review, analysis): largest reduction
- JSON/structured: moderate reduction
- Text-heavy (essays, reports): smaller reduction
- Real-time chat (short messages): little to none

### Q: "Should I use alias compression?"

**A:** Yes, unless output is user-facing. Aliases make text unreadable in logs/exports.

### Q: "How often should I update the instruction table?"

**A:** Once per week or when your templates change significantly. It's auto-reloaded every 5 minutes.

### Q: "What if compression breaks something?"

**A:** File an issue on GitHub. In the meantime, disable the offending stage and continue. Compression is designed to fail gracefully.

---

## Reference: Source Code Links

- **Pipeline orchestrator:** [`packages/core/tokenpak/agent/compression/pipeline.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/pipeline.py) (line 20–150)
- **Dedup logic:** [`packages/core/tokenpak/agent/compression/dedup.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/dedup.py)
- **Segmentizer:** [`packages/core/tokenpak/agent/compression/segmentizer.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/segmentizer.py)
- **Alias compressor:** [`packages/core/tokenpak/agent/compression/alias_compressor.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/alias_compressor.py) (line 30–80 for tuning)
- **Instruction table:** [`packages/core/tokenpak/agent/compression/instruction_table.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/instruction_table.py)
- **Directives applier:** [`packages/core/tokenpak/agent/compression/directives.py`](https://github.com/tokenpak/tokenpak/blob/main/packages/core/tokenpak/agent/compression/directives.py)

---

## Next Steps

1. **Start with the balanced config** (Example 2 above).
2. **Measure token savings** on your workload for 1 week.
3. **Adjust based on your latency tolerance:** Trade a portion of token savings for lower added latency where your path is latency-sensitive.
4. **Monitor regularly:** Token costs shift as context size changes.

---

**Questions? Issues?** Open a GitHub issue or reach out to the TokenPak team on Slack.
