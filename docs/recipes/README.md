# TokenPak Recipes

A collection of how-to guides for real-world TokenPak use cases.

> **Read this first — recipe status labels.** Each recipe is labeled at the top with one of:
>
> - **Verified runnable** — the commands and config shown work against the current TokenPak release (default proxy `http://127.0.0.1:8766`).
> - **Conceptual** — an illustrative pattern, not a copy-paste-runnable script. Some config keys, CLI verbs, or response fields shown are *design illustrations* and are **not** part of the shipped product surface. Read these for the idea, not as a tested runbook.
>
> TokenPak's proxy is a **byte-preserving passthrough**: it forwards request and response bodies verbatim and does **not** inject fields such as `cost_cents`, `status`, or `provider` into the JSON response body. Cost and usage data are recorded out-of-band (see [`tokenpak status`](../cli-reference.md) and the cost-monitoring recipe), not returned inline in the response.

## Recipe Index

| # | Recipe | Use Case | Status |
|---|--------|----------|--------|
| 1 | [Multi-Provider Fallback](./01-multi-provider-fallback.md) | Route to a backup provider on outage | Conceptual |
| 2 | [Budget Caps & Spend Alerts](./02-budget-caps.md) | Set spend limits with alerts | Conceptual |
| 3 | [Per-User Rate Limiting](./03-per-user-rate-limiting.md) | Different rate limits per user tier | Conceptual |
| 4 | [Model Routing by Use Case](./04-model-routing-by-use-case.md) | Route by task type | Conceptual |
| 5 | [Cost Monitoring & Observability](./05-cost-monitoring.md) | Track usage and cost | Conceptual |
| 6 | [Streaming Responses](./06-streaming-responses.md) | Receive responses token-by-token | Verified runnable |
| 7 | [Local Development with Mock](./07-local-development-mock.md) | Test without real API costs | Conceptual |

---

## Quick Start by Use Case

### "I want to save money"
1. Look at **[Local Development with Mock](./07-local-development-mock.md)** for a cost-free dev pattern.
2. Read **[Budget Caps](./02-budget-caps.md)** for the spend-guard pattern.
3. Consider **[Model Routing by Use Case](./04-model-routing-by-use-case.md)** to use a smaller model where it fits.

### "I want reliability"
1. Read **[Multi-Provider Fallback](./01-multi-provider-fallback.md)** for the failover pattern.
2. Read **[Per-User Rate Limiting](./03-per-user-rate-limiting.md)** for fairness across users.
3. Read **[Cost Monitoring](./05-cost-monitoring.md)** for visibility into spend.

### "I want the best user experience"
1. Start with **[Streaming Responses](./06-streaming-responses.md)** — stream tokens as they arrive.
2. Add **[Model Routing by Use Case](./04-model-routing-by-use-case.md)** — pick a model per request.
3. Add **[Cost Monitoring](./05-cost-monitoring.md)** — keep an eye on spend.

---

## How to read a recipe

Every recipe follows this structure:

1. **Status** — Verified runnable or Conceptual (see banner above).
2. **What this solves** — one-sentence summary.
3. **Prerequisites** — what you need set up.
4. **Pattern / Config** — the idea, with a config or command sketch.
5. **What's real today** — which parts are shipped product behavior vs. illustrative.

## Verifying a Verified-runnable recipe

For recipes labeled **Verified runnable**:

1. Start the proxy: `tokenpak serve` (listens on `http://127.0.0.1:8766` by default).
2. If the recipe ships a config file, check it with `tokenpak config-check <file.json>`.
3. Run the commands shown and compare against the described behavior.

Conceptual recipes are not expected to run as written — they illustrate a pattern.

## Real CLI surface

The commands referenced in these recipes that are part of the shipped CLI include:

- `tokenpak serve` — start the proxy (default `http://127.0.0.1:8766`).
- `tokenpak config-check <file.json>` — validate a proxy config file. For the proxy config it recommends a `server: { port: 8766, host: '127.0.0.1' }` block.
- `tokenpak status` — health and recorded usage.

Run `tokenpak --help` to see the full, authoritative list of subcommands for your installed version. Commands shown in **Conceptual** recipes (for example provider/model listing, spend reconciliation, or usage reports) may not exist in your installed version — always confirm with `tokenpak --help`.

---

## Questions?

- **Validate a proxy config:** `tokenpak config-check <file.json>`
- **Health check:** `tokenpak status`
- **Full command list:** `tokenpak --help`
