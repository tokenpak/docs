# Upgrading to TokenPak 1.25.0

```bash
python -m pip install --upgrade "tokenpak==1.25.0"
tokenpak --version
tokenpak doctor
```

Keep the previous environment and back up configuration and persistent state
before changing a running installation. Existing custom configuration and
pricing rows are preserved; a version upgrade does not authorize rewriting
stored costs.

## Changes to check

- `tokenpak savings --verify` compares the byte estimator with an independent
  tokenizer on a packaged corpus. Install `tokenpak[tokens]==1.25.0`; offline
  use also needs its encoding data cached. Stored prompts are not reconstructed.
- Where vault injection is enabled, retrieval has a configurable 2,000 ms
  deadline and two worker slots. Timeout or backlog forwards the original bytes
  and records a degradation reason. Configure `TOKENPAK_RETRIEVAL_TIMEOUT_MS`
  or `vault.retrieval_timeout_ms` as needed.
- Role-bearing conversation turns remain intact across companion and Pak-builder
  processing. Concurrent native launches use separate generated files; custom
  hooks are composed and customized skills are preserved during managed upgrades.
- Session displays distinguish observed usage, estimated cost and burn, guard
  runway, and session remainder. Mixed model/effort history and unsupported
  effort values remain unavailable for homogeneous forecast calibration.
- Corrected seed catalogs carry explicit unit and provenance metadata. Existing
  legacy rows keep their numeric interpretation until an explicit refresh, and
  stored costs are not rewritten. The reprocess pricing-version override remains
  ineffective; do not use it as evidence of historical repricing.

## Optional Pro daemon

Pro 0.2.0 declares support for exactly OSS 1.25.0 and TIP-1.0. Upgrade that pair
together through the licensed package index. The installed package metadata and
daemon handshake must agree before readiness is reported as active. Missing,
malformed, unconfigured, or incompatible declarations produce a diagnostic.
Compatibility does not grant a license or bypass entitlement checks.

The Pro observation and evaluation foundations retain unavailable-input states.
They do not establish measured production reroute policies, admitted empirical
priors, human comprehension results, or default-on automation.

## Rollback

```bash
python -m pip install --upgrade "tokenpak==1.24.0"
```

For a Pro installation, restore the prior Pro 0.1.6 / OSS 1.24.0 pair together
from the retained environment and configuration backup. Preserve private
observations and adverse records. Recheck version, doctor, proxy health, and
the integrations used by your installation after either upgrade or rollback.
