# Conformance

A component is **TIP-1.0 conformant** when its manifest validates against the
right schema, it publishes the capabilities its profile requires, and the headers
and telemetry it emits match the published shapes. This page walks through
verifying each of those.

Two resources on the registry make conformance checkable:

- **Test vectors** — `test_vectors/` holds fixtures for every conformance area
  plus one **golden** manifest per profile. Each area has `valid-*` cases that
  must pass and `fail-*` cases that must be rejected.
- **The validator** — [`tokenpak-tip-validator`](https://pypi.org/project/tokenpak-tip-validator/),
  a Python package that checks manifests, profile compliance, and wire headers
  against the canonical schemas.

```bash
pip install tokenpak-tip-validator
```

!!! note "For implementers only"
    You only need the validator and test vectors if you are **building** a TIP
    component. If you are using TokenPak, you do not need either.

## Step 1 — pick your profile

Decide which of the five profiles your component is, then read the capabilities
that profile is expected to publish:

| Profile | You are building… |
|---|---|
| `tip-proxy` | A data-plane proxy (compression, routing, caching, telemetry). |
| `tip-companion` | A client-side, pre-send optimizer. |
| `tip-adapter` | A bridge from a client tool or framework to a proxy. |
| `tip-plugin` | A hook-point extension. |
| `tip-dashboard-consumer` | A read-only telemetry view or alerting tool. |

See [Capabilities](capabilities.md) for the label catalog per profile.

## Step 2 — write and validate your manifest

Author the manifest for your kind (see [Profiles & manifests](profiles.md)), then
validate it against the schema:

```bash
python -m tokenpak_tip_validator --schema adapter --input my-manifest.json
```

The golden manifests are working references to author against — there is one per
profile, e.g. `test_vectors/golden/tip-proxy.json` and
`test_vectors/golden/tip-adapter.json`.

## Step 3 — check profile compliance

Confirm the capabilities you publish satisfy your profile:

```bash
python -m tokenpak_tip_validator \
    --profile tip-proxy \
    --capabilities "tip.compression.v1,tip.cache.provider-observer,tip.telemetry.wire-side"
```

This checks that every label is well-formed, that required labels for the profile
are present, and that no label is reserved for a different profile.

## Step 4 — validate the wire

If your component puts headers on the wire, validate a captured set against the
[headers schema](wire-headers.md):

```bash
python -m tokenpak_tip_validator --wire response --input captured-headers.json
```

The header vectors encode the rules from this section. They are worth reading as
a checklist:

- `headers/valid-response-full.json`, `headers/valid-response-minimal.json` — the
  shapes that must pass.
- `headers/fail-missing-cache-origin.json` — a response with no
  `X-TokenPak-Cache-Origin` is **not** conformant.
- `headers/fail-over-claim-cache-origin.json` — claiming a cache origin you cannot
  attribute is a conformance failure; honest `unknown` is required.
- `headers/fail-invalid-tip-version.json` — the version must match
  `TIP-<n>.<n>`.

## Step 5 — validate telemetry and errors

If you emit telemetry rows or error envelopes, validate samples against
[`telemetry-event-v1.json`](https://docs.tokenpak.ai/schemas/tip/telemetry-event-v1.json)
and [`error-v1.json`](https://docs.tokenpak.ai/schemas/tip/error-v1.json). The
telemetry vectors make the closed-schema and honesty rules concrete:

- `telemetry/valid-full-event.json`, `telemetry/valid-minimal-event.json` — must
  pass.
- `telemetry/fail-missing-cache-origin.json`, `telemetry/fail-null-cache-origin.json`
  — `cache_origin` is required and non-null.
- `telemetry/fail-negative-tokens.json` — token counts are non-negative.
- `telemetry/fail-addprop.json` — unknown top-level fields are rejected; use
  `ext`.

## Conformance checklist

A component is ready to call itself TIP-1.0 conformant when:

- [ ] Its manifest validates against the matching manifest schema.
- [ ] It declares an honest `compatibility.tip_version_range`.
- [ ] It publishes the capabilities its profile requires, and only well-formed
      labels.
- [ ] Every request and response carries `X-TokenPak-TIP-Version` and
      `X-TokenPak-Profile`.
- [ ] Every response classifies `cache_origin` honestly (`proxy` / `client` /
      `unknown`), never over-claiming.
- [ ] Compression savings and cache savings are reported separately, never summed.
- [ ] Every error uses the [error envelope](errors.md) with a `code` and a
      teaching `message`, and leaks no credentials in `details`.
- [ ] All `valid-*` vectors for your areas pass and all `fail-*` vectors are
      rejected.

## See also

- [Profiles & manifests](profiles.md) — what you validate in step 2.
- [Capabilities](capabilities.md) — what you check in step 3.
- Test vectors and validator live on the registry under `test_vectors/` and
  `tokenpak_tip_validator/`.
