# Upgrading to TokenPak 1.26.0

```bash
python -m pip install --upgrade "tokenpak==1.26.0"
tokenpak --version
tokenpak doctor
```

Retain the extras your application uses. The standard service profile is
`tokenpak[serve,tokens,telemetry]==1.26.0`. Back up configuration, pricing and
accounting databases, and private recommendation stores before changing a
running installation. Stop writers or use a consistent database backup method.
Keep the previous environment and artifacts through the observation period.

## Native observations and accounting

This release adds authenticated guard and workload observations for an explicit
session, optional durable reservations, and workload-conditioned price quotes.
Durable accounting remains off by default. Enabling it requires a reviewed
configuration and complete applicable evidence; installing the package alone
does not enable it or authorize spending.

The native observation routes require loopback access and the configured
`X-TPK-Key`, including when ordinary loopback proxy access is otherwise allowed.
They reject browser-origin requests and return non-cacheable data. Disabled
workload accounting returns an explicit unavailable response. Reads do not add
provider requests or change the accounting store.

[Request workload observations](request-workload-observations.md) describe
supported provider, token, cache, region and service-tier facts.
[Workload pricing](workload-pricing.md) explains conditional catalog bands and
cache accounting. Missing facts remain missing; a cache directive does not prove
a cache hit. Estimates without complete price receipts cannot be treated as a
verified monetary baseline for positive durable caps.

Schema additions preserve existing rows. Existing pricing databases receive
new bundled bands only through an explicit versioned seed refresh; ordinary
initialization does not replace historical prices. Frozen session reads preserve
the selected rows throughout their calculation.

## Optional Pro pair

Pro 0.4.0 requires exactly OSS 1.26.0 and TIP-1.0. Upgrade both packages through
the existing licensed distribution path. Verify actual import origins, package
versions and the daemon handshake. Compatibility does not grant a license.
The previous Pro 0.3.0 declares OSS 1.25.3 only.

The new explicit recommendation workflow resolves current policy, native guard
and history facts, a target, complete approved prices and eligible empirical
priors. It can prepare a local context bundle, record observed-reference
measurements, recheck facts before confirmation, and retain a decline record.
Unknown or stale prerequisites remain unavailable; strict stops remain terminal.
Commands do not launch another session, transfer execution, or enable automatic
rerouting. CLI, JSON and dashboard comparisons share the same measured record.
Their scenario bounds are not calibrated confidence intervals, total future
bills or verified savings. Human comprehension and realized task quality still
require their own evidence.

## Known optional dependency findings

The release accepts the open High NLTK advisory
[GHSA-8mgp-746c-j5xp](https://github.com/advisories/GHSA-8mgp-746c-j5xp) in
optional compression/full and llamaindex integrations for this release only.
A separate Moderate Accelerate advisory
[GHSA-4j2p-28q2-5m79](https://github.com/advisories/GHSA-4j2p-28q2-5m79) concerns
untrusted sharded checkpoint paths in optional compression/full integrations.
The base and standard service profiles do not select these optional paths.
See the released [security policy](https://github.com/tokenpak/tokenpak/blob/v1.26.0/SECURITY.md)
for affected versions, trusted-model requirements, the consumer's remote-code
default and the limits of the exception. Neither finding is represented as fixed.

## Rollback

```bash
python -m pip install --upgrade "tokenpak==1.25.3"
```

Restore Pro 0.3.0 and OSS 1.25.3 together when Pro is installed. Retain newly
created records separately before restoring the previous consistent state and
configuration backups: old versions do not implement the new native record
semantics. Verify doctor, CLI, proxy, package origins and integrations after
rollback. The [1.25.3 guide](upgrading-1.25.3.md) preserves that release's context.
