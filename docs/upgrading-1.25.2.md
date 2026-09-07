# Upgrading to TokenPak 1.25.2

```bash
python -m pip install --upgrade "tokenpak==1.25.2"
tokenpak --version
tokenpak doctor
```

Keep the previous environment and back up configuration and persistent state
before changing a running installation. Existing custom configuration and
pricing rows are preserved. An upgrade does not recalculate stored request costs.

## Changes to check

- Proxy cost estimates honor explicit cache-read and cache-write prices from
  the resolved catalog entry, including zero-valued prices. Missing explicit
  cache rates retain their existing fallback estimates. Catalog data are
  unchanged; unsupported cache lifetimes and long-context tiers are not added.
- Ordinary Codex launcher upgrades reconcile unchanged legacy skill copies
  after installing canonical copies. Customized copies are preserved with
  conflicts reported. Exports to a separate directory retain their behavior.

The [1.25.1 upgrade guide](upgrading-1.25.1.md) describes the preceding release's
broader changes and limitations. No public API signature or telemetry schema
changes in this patch.

## Optional Pro daemon

Pro 0.2.1 declares support for exactly OSS 1.25.2 and TIP-1.0. Upgrade the pair
together through the licensed distribution path. Check installed package
origins, declared compatibility and the daemon handshake before treating the
pair as active. Compatibility does not grant a license or bypass entitlement
checks. Pro 0.2.0 declares OSS 1.25.1 only.

Production Reroute recommendations still require complete measured inputs and
eligible empirical priors. This patch does not supply human comprehension or
production outcome evidence, or enable automation by default.

## Rollback

```bash
python -m pip install --upgrade "tokenpak==1.25.1"
```

For a Pro installation, restore Pro 0.2.0 and OSS 1.25.1 together from retained
artifacts, with the saved environment and configuration. Preserve observations
and existing records. Recheck version, doctor, proxy health and your integrations
after either upgrade or rollback. The earlier 1.25.0 tag remains retired without
a package release; do not use it as a rollback target.
