# Recipe: Cost Monitoring & Observability

> **Status: Conceptual.** This recipe describes a cost-observability *pattern*. The declarative `metrics:` / `prometheus:` / `custom_metrics:` config block, a built-in Prometheus metrics endpoint, and the specific `tokenpak_*` metric values shown below are **illustrative** — they are not part of the validated config surface of the current TokenPak release, and the proxy does **not** expose a built-in Prometheus exporter (there is no `:8001/metrics` endpoint). The real, shipped way to see usage and cost is `tokenpak status`. Confirm any CLI command against `tokenpak --help`.

**What this solves:** The pattern of getting visibility into request volume, token usage, and cost over time.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- API keys for your providers
- (For the conceptual dashboard pattern) a metrics store such as Prometheus + Grafana

## What's real today

The shipped proxy listens on `http://127.0.0.1:8766` and records usage out-of-band. To see it:

```bash
tokenpak serve     # proxy on http://127.0.0.1:8766

# After sending some traffic through the proxy:
tokenpak status    # recorded request, token, and cost summary
```

TokenPak's proxy is a **byte-preserving passthrough** — it does not inject cost fields into the response body, and it does not run a separate Prometheus metrics server. Usage/cost accounting is recorded server-side and surfaced via the CLI (`tokenpak status`), not scraped from a `:8001/metrics` endpoint.

## The pattern (illustrative — external metrics pipeline)

If you want dashboards in Prometheus/Grafana, the **conceptual** pattern is to export TokenPak's recorded usage into a metrics store with your own shim (for example, a small exporter that reads TokenPak's recorded usage and republishes it as Prometheus metrics). The config and metric names below are **illustrative only** — they do not describe a built-in TokenPak exporter:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema,
# and not a built-in TokenPak metrics exporter.
metrics:
  enabled: true
  prometheus:
    enabled: true
    port: 9464          # your own exporter's port (example)
  track_by: [user_id, model, provider, status_code]
```

```yaml
# Example Prometheus scrape config pointing at YOUR exporter (illustrative):
scrape_configs:
  - job_name: tokenpak
    static_configs:
      - targets: ['localhost:9464']   # your exporter, not a TokenPak built-in
```

Example metric series your exporter might publish (names and values are **illustrative**, not emitted by TokenPak itself):

```
# ILLUSTRATIVE metric shapes — define and emit these yourself
tokenpak_requests_total{model="...",provider="...",status="200"}
tokenpak_cost_usd_total{model="...",provider="..."}
tokenpak_tokens_sent_total{model="..."}
```

## Designing cost observability

Whether you use `tokenpak status` directly or build an external pipeline, these principles apply:

- **Watch cardinality.** Per-user-id series can explode; aggregate by tier or model where you can.
- **Don't scrape too aggressively.** A modest interval captures trends without overhead.
- **Tie alert thresholds to your budget**, not to arbitrary round numbers.
- **Always track cost, not just request counts** — requests are not a proxy for spend.
- **Retain long-term data** if you need historical trends; short default retention loses history.
- **Keep a user or tier dimension** so you can spot a single heavy consumer.
