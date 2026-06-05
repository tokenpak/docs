# Recipe: Local Development with a Mock Provider

> **Status: Conceptual.** This recipe describes a cost-free local-testing *pattern*. The declarative `mock` provider with canned `responses:` / `patterns:`, the `enabled: false` / `fallback_provider` config keys, the inline `content` / `cost_cents` response fields, and the `tokenpak logs --provider` command shown below are **illustrative** — they are not part of the validated config surface or shipped CLI of the current TokenPak release. There is no built-in `mock` provider type in the current proxy config schema. Confirm any CLI command against `tokenpak --help`.

**What this solves:** The pattern of testing your integration against a stub instead of a real provider, so development costs nothing and is deterministic.

## Prerequisites
- TokenPak installed (`tokenpak --help`)
- A local environment for testing

## The pattern (illustrative config)

The idea is to point your dev environment at a stub that returns canned responses, then swap to real providers in production with no application code change. The YAML below is a **conceptual** illustration only — a built-in `mock` provider type is not part of the validated TokenPak config surface:

```yaml
# ILLUSTRATIVE ONLY — not a validated TokenPak config schema.
# A built-in "mock" provider type does not exist in the current release.
providers:
  mock:
    type: mock
    latency_ms: 200
    responses:
      gpt-4:
        default: "Mock GPT-4 response"
        patterns:
          debug: "Mock response: Debugged your code"
```

## What's real today

- Start the proxy with `tokenpak serve` (default `http://127.0.0.1:8766`).
- The proxy is a byte-preserving passthrough: responses are the upstream provider's bodies, unchanged. TokenPak does **not** inject a `content` or `cost_cents` field, and there is no `tokenpak logs --provider` verb. Use `tokenpak status` for recorded usage.
- Validate a proxy config file with `tokenpak config-check <file.json>`. The `mock` provider block above is **not** part of that validated surface.

### A real way to get the same benefit today

Run your own local stub server that speaks the provider's HTTP API, and point your client (or the proxy's upstream URL) at it during development. Your application code stays identical; only the endpoint differs between dev and prod.

```python
# stub_server.py — a tiny deterministic stand-in for the provider API.
# Run this locally and point your app/proxy upstream at it in dev.
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        _ = self.rfile.read(length)  # ignore body; return a canned reply
        body = json.dumps({
            "id": "msg_stub",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Mock response for local dev"}],
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()
```

Your application talks to the proxy (`http://127.0.0.1:8766`) the same way in dev and prod; you switch the upstream between the stub and the real provider via configuration/environment, with no code change.

## Designing a dev-mock strategy

- **Keep mocks realistic.** Include error cases and varied response lengths, not just a single "success."
- **Don't ship dev config to prod.** Make CI/CD select the production config explicitly.
- **Simulate latency.** A zero-latency stub can hide slow code paths that only appear against a real provider.
- **Don't leave real providers reachable in dev** if the point is to avoid spend — make the dev path point only at the stub.
- **Vary responses** by input where it matters, so tests exercise more than one branch.
- **Be able to simulate failures** (e.g. a stub that returns errors some of the time) so you can test your fallback/retry logic.
