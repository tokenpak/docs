# TokenPak Security Notes

## Header Security

### Server Version Disclosure (Fixed 2026-03-26)

**Issue:** Default `BaseHTTPServer` emitted `Server: BaseHTTP/0.6 Python/3.12.3` in all responses, leaking runtime version.

**Fix:** `ForwardProxyHandler.server_version = "TokenPak"` and `sys_version = ""` — response header is now `Server: TokenPak`.

**Verification:**
```
HTTP/1.0 200 OK
Server: TokenPak
```

### Upstream Authorization Headers

**Status:** ✅ Not forwarded to clients

The proxy **strips** the following headers from upstream responses before relaying to the client:
- `Authorization`
- `X-Api-Key`
- `Anthropic-Api-Key`
- `Server`
- `X-Powered-By`

Outgoing requests to upstream also strip: `host`, `proxy-authorization`, `proxy-connection`, `connection`, `keep-alive`, `transfer-encoding`, `accept-encoding`.

### Security Headers

**`X-Content-Type-Options: nosniff`** is added to all proxied responses.

### Internal Path Exposure

The `/health` and `/stats` endpoints expose operational data (token counts, cost, circuit breaker state). These endpoints are **localhost-only** by design — the proxy binds to `127.0.0.1:8766` and is not externally accessible.

## Auth Key Handling

API keys are passed to upstream providers in outbound requests. They are:
- Never logged
- Never echoed in responses
- Read from your local environment (for example, a local `.env` file) and never written to configuration files committed to version control

## Known Limitations

- No HTTPS on the proxy listener (localhost-only, low risk)
- `/stats` exposes cost and token data (localhost-only, acceptable)

## Reporting a Vulnerability

If you discover a security issue in TokenPak, please report it privately by email to **security@tokenpak.ai**. Include a description of the issue, steps to reproduce, and the affected version.

Please do not open a public issue for security reports.

We aim to acknowledge reports within a few business days and to share a remediation timeline after triage. These are response targets, not guarantees — TokenPak is an open-source beta maintained on a best-effort basis.

## Supported Versions

Security fixes are applied to the current OSS beta release line (the `1.13.x` series, currently `1.13.0`, installed via `pip install tokenpak`). Older pre-beta versions are not maintained.
