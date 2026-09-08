# Upgrading to TokenPak 1.25.3

```bash
python -m pip install --upgrade "tokenpak==1.25.3"
tokenpak --version
tokenpak doctor
```

Keep the previous environment and back up configuration and persistent state
before changing a running installation. Existing configuration, pricing rows
and recorded costs are preserved. This release requires no data migration.

## Changes to check

- Spend Guard retains an in-flight reservation until its telemetry row commits.
  A successful commit refreshes rolling-cap usage before releasing that
  reservation. Failed writes retain the existing bounded reservation.
- Session economics displays pair burn-direction arrows with words and expand
  context-limit labels. Machine values and provider payloads remain unchanged.

Reservations retain their existing process ownership and expiry limits. The
fix does not add a cross-process live guard snapshot or make the forecast
include every pending request. The [1.25.2 guide](upgrading-1.25.2.md) records
the preceding cache-pricing and companion upgrade corrections.

## Optional Pro daemon

Pro 0.3.0 declares support for exactly OSS 1.25.3 and TIP-1.0. Upgrade the pair
together through the licensed distribution path. Verify installed package
origins, compatibility and the daemon handshake. Compatibility does not grant
a license or bypass entitlement checks. Pro 0.2.1 declares OSS 1.25.2 only.

Pro's new absolute-price construction API requires complete cache and generator
prices and retains supplied provenance. Same-model recap generation uses a
cache discount only when the cache is known warm; other states account for the
larger uncached or cache-write charge. Alternate generators can supply their
own output price, including zero.

These changes do not authenticate a price catalog, resolve model or tokenizer
compatibility, supply measured inputs or empirical priors, or enable production
recommendations. Human comprehension and production outcome evidence remain
separate requirements. Automation defaults are unchanged.

## Rollback

```bash
python -m pip install --upgrade "tokenpak==1.25.2"
```

For a Pro installation, restore Pro 0.2.1 and OSS 1.25.2 together from retained
artifacts, with the saved environment and configuration. Preserve observations
and existing records. Recheck versions, doctor, proxy health and integrations
after either upgrade or rollback. Keep backups through the observation period.
