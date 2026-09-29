# TokenPak Savings

**How much will TokenPak save you?**

It depends on your workload — specifically how much of your context repeats and how compressible it is. The honest answer is: measure it on your own traffic. TokenPak gives you the tools to do exactly that.

The default proxy preserves conversation turns, so a forwarded request can truthfully report zero tokens saved. Explicit context tools can reduce eligible content.

> **A note on numbers:** TokenPak does not publish headline savings or cost figures until they are backed by a validated, frozen-fixture benchmark run. Our benchmark suite is in progress; receipt-backed figures will publish once it produces a validated run. Until then, the most reliable savings number is the one you measure on your own workload with `tokenpak savings`.

---

## The Math (Simple Version)

### What TokenPak Does

1. **Records every request** — Records each request that goes through the proxy, including measured usage and estimated cost
2. **Preserves conversation turns by default** — A forwarded request can correctly report zero tokens saved
3. **Reduces eligible content on request** — Explicit compression operations can reduce eligible content
4. **Reports recorded usage** — `tokenpak savings` shows recorded usage, and `tokenpak status --tip-cache` shows provider-cache attribution

### The Impact

Explicit context tools can reduce eligible content:

| Technique | What it does | When it helps |
|-----------|--------------|---------------|
| **Text deduplication** | Removes repeated content within eligible input | When that input contains repetition |
| **Explicit compression** | Reduces eligible content | Where the content is eligible |

How much each of these saves depends entirely on your workload and repeat rate — there is no single number that holds across all traffic.

---

## How Savings Behave in Practice

Savings depend on your workload. On the default path, a forwarded request can report zero tokens saved.

- Repeated content may offer opportunities for explicit compression; measure the result on your own workload.
- Provider cache reuse is distinct from TokenPak context reduction; inspect attribution with `tokenpak status --tip-cache`.

The only way to know your number is to run TokenPak on your traffic and read `tokenpak savings`.

---

## How to Measure Your Own Savings

### 1. Start the Proxy

```bash
export ANTHROPIC_API_KEY=sk-ant-...
tokenpak serve
```

### 2. Point Your Code at It

```python
# Before: Uses real API directly
client = Anthropic()

# After: Routes through the TokenPak proxy
client = Anthropic(base_url="http://localhost:8766")
```

### 3. Check Your Savings (Real-Time)

```bash
# One-liner to see your savings today
tokenpak savings

# Or scope it to the current session/day
tokenpak stats --today
```

The output reports the requests, tokens, and estimated cost saved for *your* traffic, and zero is a valid result — these are the numbers that matter for your decision.

### 4. Understand the Breakdown

Inspect recorded usage with `tokenpak savings` and provider-cache attribution with `tokenpak status --tip-cache`.

---

## Example: Agent Loop

Consider an agent that:

1. Takes a user question
2. Searches a knowledge base
3. Calls Claude several times to refine the answer

**Without TokenPak:** Every Claude call re-sends the full search context, so you pay for the same large context on each call.

**With TokenPak:** The proxy records each call. Provider cache reuse is distinct from TokenPak context reduction; inspect attribution with `tokenpak status --tip-cache`.

The actual saving depends on how much context repeats across your calls and on the explicit context tools you use. Run `tokenpak savings` against your own agent to see the real figure, which can be zero.

---

## Setup Options

### Option 1: Proxy (Recommended)

Sit TokenPak between your code and the LLM API. No code changes.

```bash
tokenpak serve --port 8766
```

Then swap one URL in your client:

```python
client = Anthropic(base_url="http://localhost:8766")
```

**Pros:** No code changes beyond the base URL; every request through the proxy is recorded
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

TokenPak ships with compression profiles tuned for different workloads. Heavier compression generally trades more aggressively for savings; lighter compression prioritizes fidelity. In the reference setup, the built-in Pak builder leaves every system, user, and assistant turn intact even under the `aggressive` profile, so the receipt reports zero tokens saved.

| Profile | Compression | Risk | Use Case |
|---------|-------------|------|----------|
| **safe** | Light | Very low | Production, high-stakes queries |
| **balanced** | Medium | Low | General workloads (default) |
| **aggressive** | Strong | Medium | Batch processing, bulk summarization |
| **agentic** | Medium-strong | Low–medium | Agent loops, tool use, reasoning |

Set your profile:

```bash
export TOKENPAK_PROFILE=balanced  # default
tokenpak serve
```

Or per-request:

```python
# This request uses aggressive compression
response = client.messages.create(
    model="claude-opus-4-8",
    messages=[...],
    extra_headers={"X-TokenPak-Profile": "aggressive"}
)
```

---

## Estimating Your ROI

To estimate your own return, measure first, then extrapolate:

1. Run TokenPak over a representative slice of your traffic.
2. Read your measured saving from `tokenpak savings`; it can be zero on the default path.
3. Apply that measured rate to your monthly LLM spend.

Deploying the proxy is low-effort — typically a single URL swap in your client — so you can measure your real savings rate before committing to a wider rollout.

---

## Caveats & Tradeoffs

### When Savings Are Lower

- ⚠️ The default proxy path (conversation turns are preserved, so a forwarded request can report zero tokens saved)
- ⚠️ Provider cache reuse (distinct from TokenPak context reduction; inspect attribution with `tokenpak status --tip-cache`)

### Quality Tradeoffs

The default proxy preserves conversation turns. Explicit compression operations change eligible content, so they can change what the model sees. Test any compression setting on your workload before relying on it.

---

## Next Steps

1. **Start simple:** `tokenpak serve` + swap one URL
2. **Measure:** Run `tokenpak savings` / `tokenpak stats` after a few requests
3. **Optimize:** Test different profiles with your workload
4. **Scale:** Deploy to production when comfortable

---

## Questions?

- **How do I verify the savings are real?** → Inspect recorded usage with `tokenpak savings` and provider-cache attribution with `tokenpak status --tip-cache`
- **Will this slow down my requests?** → The proxy adds a network hop; the added latency depends on your deployment path (run it on the same machine/network to minimize it). SDK mode adds no network hop.
- **Can I bypass TokenPak for specific requests?** → Yes, set header `X-TokenPak-Bypass: true`
- **What if the LLM needs the exact original tokens?** → Use bypass header or switch to `safe` profile
- **Does this work with streaming?** → Yes, with caveats (cache hits are less frequent in stream mode)

See [Troubleshooting](./troubleshooting.md) for more.
