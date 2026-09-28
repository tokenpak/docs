---
title: Upgrade TokenPak
rung: 2
audience: Developers upgrading an existing TokenPak installation.
updated: 2026-09-28
status: current
---

# Upgrade to TokenPak 1.30.0

This guide is for developers upgrading from TokenPak 1.29.0.

## Execution ledger recovery signal

A durable, SQLite-backed execution ledger records in-flight upstream proxy
calls before dispatch. If the proxy restarts mid-stream, a retried request now
receives an explicit `terminally_failed` / `recovery_status` signal instead of
a bare connection reset. This is a fail-with-signal correction: it does not
implement transparent replay or a full exactly-once resume state machine.

This release also carries a set of backward-compatible fixes: semantic-cache
keys now include model/provider identity so a cached response cannot be served
for a different model; `tip_spend_guard.*` configuration rejects unknown keys
instead of silently ignoring them; spend-guard audit rows carry an explicit
reason and projected-token count on every decision path; the background OAuth
refresher is wired into the thread-based proxy server; savings, compare and
leaderboard reads are retargeted onto the canonical monitor store; and
vault-index load failures now emit explicit telemetry instead of a silent
print. None of these change the public CLI, HTTP, or configuration surface.

## Install and verify

1. Retain the previous package pair and environment for rollback.
2. Install `tokenpak==1.30.0` with the extras already used by your
   installation. The standard service profile is
   `tokenpak[serve,tokens,telemetry]==1.30.0`.
3. If you use Pro, install Pro 0.5.1 together with OSS 1.30.0 through your
   existing licensed delivery channel; upgrade the pair together. Pro 0.5.1
   supports OSS 1.26.0 through 1.30.0 with TIP-1.0. Pro 0.5.0 supports OSS
   only through 1.29.0 — if you stay on Pro 0.5.0, stay on OSS 1.29.0 as well.
4. After active requests finish, restart the services that use the replaced
   environment. Reinstall or repoint configured companion hooks when changing
   environment paths. Preserve explicit journal-root settings and verify the
   hooks and service read the intended existing journal.
5. Run `tokenpak --version`, `tokenpak doctor`, and
   `tokenpak status --json --session ID` for a session you intend to inspect.
   Start a new managed client launch to use updated hooks and display code.

This is a package-only upgrade: no database migration and no configuration
change are required. TokenPak 1.30.0 creates a new `execution_ledger.db` in
its state directory the first time it starts; existing state and configured
journal locations are otherwise unaffected.

## Roll back

Reinstall OSS 1.29.0. Rollback was verified with the `execution_ledger.db`
file 1.30.0 creates left in place — 1.29.0 serves normally with that file
present, so no state needs to be removed. If you run Pro, roll back to the
pair of OSS 1.29.0 with either Pro 0.5.0 or Pro 0.5.1. Restore the previous
environment pointer and hook configuration after active requests finish.
Published artifacts and tags are never overwritten.

## Limits and dependency findings

A `terminally_failed` or `recovery_status` signal on a retried request means
the execution ledger detected a proxy restart mid-stream. It is not
transparent replay and not a full exactly-once resume: the original in-flight
call is not silently completed or resumed for you. See
[known limitations](KNOWN_LIMITATIONS.md#execution-ledger-recovery-is-fail-with-signal-not-replay)
before treating a recovery signal as a completed retry.

Optional dependency findings are documented in
[SECURITY.md](https://github.com/tokenpak/tokenpak/blob/v1.30.0/SECURITY.md).
Release validation covers changed behavior, installed artifacts, paired
compatibility, upgrade and rollback. Publication, deployment and the
observation period remain separate milestones.
