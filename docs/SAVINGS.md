# TokenPak Savings

**How much will TokenPak save you?**

It depends on your workload — specifically how much of your context repeats and how compressible it is. The honest answer is: measure it on your own traffic. TokenPak gives you the tools to do exactly that.

> **A note on numbers:** TokenPak does not publish headline savings or cost figures until they are backed by a validated, frozen-fixture benchmark run. Our benchmark suite is in progress; receipt-backed figures will publish once it produces a validated run. Until then, the most reliable savings number is the one you measure on your own workload with `tokenpak stats` and `tokenpak report --json`.

---

## The Math (Simple Version)

### What TokenPak Does

1. **Deduplicates requests** — If you send the same prompt twice, the second one can be served from cache instead of re-sent (cache hit)
2. **Compresses long context** — Summarizes repetitive text blocks before sending to the LLM API
3. **Injects smart context** — Reuses cached blocks from your vault instead of recomputing every time
4. **Tracks every optimization** — Reports how many tokens and how much money you saved, per request

### The Impact

Savings come from two complementary mechanisms:

| Technique | What it does | When it helps |
|-----------|--------------|---------------|
| **Request deduplication** | Avoids resending an identical prompt | Every time you ask the same question twice |
| **Semantic compression** | Shrinks repetitive or verbose context | When you send large documents or code contexts |
| **Vault injection caching** | Reuses cached context blocks | In agent loops, batch processing, or knowledge-base lookups |
| **Combined (balanced mode)** | Applies caching + light compression by default | Across all requests |

How much each of these saves depends entirely on your workload and repeat rate — there is no single number that holds across all traffic.

---

## How Savings Behave in Practice

TokenPak's savings are workload-dependent. The general shape:

- **Highly repetitive traffic** (agent loops, batch jobs, knowledge-base lookups) benefits most, because cached and compressible context dominates.
- **Provider-cached flows** show lower incremental gains, because the provider is already discounting repeated context.
- **One-off, highly unique requests** benefit least, because there is little to dedup or compress.

The only way to know your number is to run TokenPak on your traffic and read the report.

---

## How to Measure Your Own Savings

### 1. Start the Proxy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
tokenpak proxy
```

### 2. Point Your Code at It

```python
# Before: Uses real API directly
client = Anthropic()

# After: Routes through TokenPak proxy (drop-in compatible)
client = Anthropic(base_url="http://localhost:8766")
```

### 3. Check Your Savings (Real-Time)

```bash
# One-liner to see your savings today
tokenpak savings

# Or scope it to the current session/day
tokenpak stats --today
```

The output reports the requests, tokens, and estimated cost saved for *your* traffic — these are the numbers that matter for your decision.

### 4. Understand the Breakdown

```bash
# Detailed report with per-model savings
tokenpak report --json
```

Returns:

- `input_tokens` — Tokens you actually sent to the API (after compression)
- `saved_tokens` — Tokens we didn't send (already cached or compressed)
- `compression_ratio` — How aggressively we compressed your context
- `cost_saved` — Estimated dollar amount saved
- `cache_hit_rate` — Share of your requests that hit the cache

Because these are computed from your own traffic, they are the authoritative measure of what TokenPak does for you — far more reliable than any generic headline figure.

---

## Example: Agent Loop

Consider an agent that:

1. Takes a user question
2. Searches a knowledge base
3. Calls Claude several times to refine the answer

**Without TokenPak:** Every Claude call re-sends the full search context, so you pay for the same large context on each call.

**With TokenPak:** The first call sends the full context; subsequent calls reuse it from cache instead of re-sending it. The more calls reuse the same context, the larger the cumulative saving.

This is the workload shape where TokenPak helps most — but the actual saving depends on how much context repeats across your calls. Run `tokenpak report --json` against your own agent to see the real figure.

---

## Setup Options

### Option 1: Proxy (Recommended)

Sit TokenPak between your code and the LLM API. No code changes.

```bash
tokenpak proxy --port 8766
```

Then swap one URL in your client:

```python
client = Anthropic(base_url="http://localhost:8766")
```

**Pros:** Works with any SDK, automatic for all requests, easy to scale
**Cons:** One extra network hop; the added latency depends on your deployment path (run the proxy on the same machine/network to minimize it)

### Option 2: SDK Mode

Call TokenPak's compression directly in your code.

```python
from tokenpak import HeuristicEngine

engine = HeuristicEngine()
compressed = engine.compress(long_context, target_tokens=2048)

# Send your LLM request with the compressed context
```

**Pros:** Fine-grained control, no proxy overhead, works offline
**Cons:** Requires code changes, manual compression at call sites

### Option 3: Hybrid

Proxy for most requests + SDK mode for special cases (cost-critical paths).

---

## Profiles: Tune Savings vs. Risk

TokenPak ships with compression profiles tuned for different workloads. Heavier compression generally trades more aggressively for savings; lighter compression prioritizes fidelity.

| Profile | Compression | Risk | Use Case |
|---------|-------------|------|----------|
| **safe** | Light | Very low | Production, high-stakes queries |
| **balanced** | Medium | Low | General workloads (default) |
| **aggressive** | Strong | Medium | Batch processing, bulk summarization |
| **agentic** | Medium-strong | Low–medium | Agent loops, tool use, reasoning |

Set your profile:

```bash
export TOKENPAK_PROFILE=balanced  # default
tokenpak proxy
```

Or per-request:

```python
# This request uses aggressive compression
response = client.messages.create(
    model="claude-opus-4-6",
    messages=[...],
    extra_headers={"X-TokenPak-Profile": "aggressive"}
)
```

---

## Estimating Your ROI

To estimate your own return, measure first, then extrapolate:

1. Run TokenPak over a representative slice of your traffic.
2. Read your measured saving from `tokenpak savings` / `tokenpak report --json`.
3. Apply that measured rate to your monthly LLM spend.

Deploying the proxy is low-effort — typically a single URL swap in your client — so you can measure your real savings rate before committing to a wider rollout.

---

## Caveats & Tradeoffs

### When Savings Are Highest

- ✅ Agent loops and multi-turn workflows
- ✅ Batch processing with repeated contexts
- ✅ Knowledge-base lookups with large doc chunks
- ✅ Codebase indexing and semantic search

### When Savings Are Lower

- ⚠️ One-off requests (no cache hits, no dedup)
- ⚠️ Highly unique contexts (compression is less effective)
- ⚠️ Provider-cached flows (the provider already discounts repeated context, so incremental gains are smaller)
- ⚠️ Streaming responses (cache benefits hit less often)

### Quality Tradeoffs

TokenPak is **semantically lossless** in `safe` and `balanced` modes:

- No information loss
- No hallucinations introduced
- All model capabilities preserved

In `aggressive` mode, TokenPak compresses more heavily to favor cost savings, which can affect accuracy on some tasks. Test it on your workload before relying on it.

---

## Next Steps

1. **Start simple:** `tokenpak proxy` + swap one URL
2. **Measure:** Run `tokenpak savings` / `tokenpak stats` after a few requests
3. **Optimize:** Test different profiles with your workload
4. **Scale:** Deploy to production when comfortable

---

## Questions?

- **How do I verify the savings are real?** → Check `tokenpak savings`, `tokenpak stats`, or `tokenpak report --json` for a token-by-token breakdown of your own traffic
- **Will this slow down my requests?** → The proxy adds a network hop; the added latency depends on your deployment path (run it on the same machine/network to minimize it). SDK mode adds no network hop.
- **Can I bypass TokenPak for specific requests?** → Yes, set header `X-TokenPak-Bypass: true`
- **What if the LLM needs the exact original tokens?** → Use bypass header or switch to `safe` profile
- **Does this work with streaming?** → Yes, with caveats (cache hits are less frequent in stream mode)

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more.
