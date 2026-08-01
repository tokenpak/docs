# TokenPak — Latency

## TL;DR

TokenPak runs as a proxy in front of your model provider. Like any network
proxy, it can add **network round-trip overhead** between your application and
the upstream API — how much depends entirely on your deployment path (where the
proxy runs relative to your app and the provider, and whether connections are
reused).

Two things are worth measuring **separately**, and we keep them separate here:

- **TokenPak's own processing** — routing, token counting, cache lookup, and
  context handling. This is distinct from the network it sits on.
- **End-to-end latency** — the wall-clock difference an application sees, which
  is dominated by network hops and connection behavior, not by TokenPak's
  internal work.

We do **not** publish specific latency numbers yet. Any figure we publish will
be backed by a reproducible benchmark receipt (see
[Benchmarks](#benchmarks-coming-soon) below) rather than an ad-hoc measurement.

---

## What affects the latency you see

- **Deployment path.** Running the proxy on the same machine or local network as
  your application avoids most avoidable network overhead. A proxy reached over
  the public internet adds more round-trip time than one on `localhost`.
- **Connection reuse.** Warm, pooled connections behave very differently from
  cold ones. Throughput under sustained load benefits from connection pooling.
- **Cache hits.** On a cache hit, TokenPak avoids re-sending and recomputing
  context, which removes work from the request path.
- **Workload shape.** Batch, async, and chat workloads tolerate added latency far
  more readily than hard real-time paths.

## Minimizing avoidable overhead

- **Run it close to your app.** Same-machine or same-network deployment keeps the
  added network round-trip small.
- **Reuse connections.** Keep the proxy warm under load rather than paying
  cold-start costs per request.
- **Lean on caching.** Repeated-context workloads benefit most, since cache hits
  take work off the request path.

## When the proxy is a good fit

**Good fits**

- Batch processing and overnight jobs
- Chat and agent workflows, where human/interaction latency dominates
- Development and testing
- Production workloads where token-cost savings outweigh added latency

**Be deliberate for**

- Hard real-time paths with strict, latency-sensitive SLAs
- Latency-sensitive UIs — in these cases, run the proxy on the same
  machine/network, or use a deployment path that avoids extra network hops

---

## Benchmark evidence

TokenPak requires a frozen-fixture benchmark run before publishing a latency,
throughput, or cost figure so the result is reproducible rather than a one-off
measurement. This page does not yet carry a validated run, so:

- We deliberately **do not** quote a specific latency overhead.
- The best way to understand TokenPak's impact on **your** workload is to measure
  it in your own environment and deployment path.

Any figure added here must include the receipt and run identity needed to
reproduce it.

---

## FAQ

**Q: Does the proxy add latency vs. calling the API directly?**
A: It can, because it adds a network hop — how much depends on your deployment
path. On cache hits, the work TokenPak would otherwise do is taken off the
request path. We don't quote a specific number until it's benchmark-backed.

**Q: Should I use the proxy if latency matters?**
A: For batch, async, agent, and chat workloads, added latency is typically not
the deciding factor. For hard real-time paths, run the proxy on the same
machine/network, or choose a deployment path that avoids extra network hops.

**Q: How do I know what it costs me?**
A: Measure it in your own environment and deployment path. Receipt-backed
figures from the benchmark suite will follow.
