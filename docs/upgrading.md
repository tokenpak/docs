---
title: Upgrade TokenPak
rung: 2
audience: Developers upgrading an existing TokenPak installation.
updated: 2026-10-07
status: current
---

# Upgrade to TokenPak 1.30.2

This guide is for developers upgrading from TokenPak 1.30.1. OSS 1.30.2 has no
published Pro pair yet: Pro 0.5.2 supports OSS 1.26.0 through 1.30.1 and
refuses 1.30.2. If you use Pro, stay on OSS 1.30.1 and Pro 0.5.2 until a Pro
release that supports 1.30.2 is published. If you do not use Pro, upgrade as
described in [Install and verify](#install-and-verify). If you are upgrading
from an earlier release, also read the 1.30.1, 1.30.0, 1.29.0 and 1.28.0
changes below.

## License activation keeps an installed license

`tokenpak activate` no longer replaces a license that is installed and still
current. Activating a different key leaves `license.json` unchanged and names
`tokenpak deactivate` as the way to replace the license. Activating the key
that is already installed reports that it is already active. An expired or
pending license can still be replaced by activating a new key.

## Expired licenses read as expired

`tokenpak license` and `tokenpak features` honor the license's `expires_at`
date and the issuer's `grace_days`. A lapsed license reads as expired and no
longer grants Pro through its tier. A license whose `expires_at` cannot be read
counts as expired.

## License writes and the Pro daemon connection file

License writes are serialized under one lock, and an unverified write never
replaces a signed license, even with a matching key. A license write now also
creates an empty `license.json.lock` file beside `license.json`; leave it in
place. On Windows, a license write takes a cross-process lock and waits up to
30 seconds for it. If it cannot get the lock, the write fails and the license
is left unchanged.

The Pro daemon's connection file (`pro/daemon.sock-info`) is now looked up under
the selected TokenPak home (`TOKENPAK_HOME`, otherwise the home that holds your
state) instead of always under `~/.tokenpak`.

## Package summary

The package summary that PyPI and `pip show tokenpak` display, and
`tokenpak.__description__`, no longer claim automatic cost cuts or default
compression and routing. They now read: "Local proxy for coding agents that
records each request and shows how far the session can go: measured usage,
estimated cost, burn and runway."

## Dependencies in existing environments

Upgrading TokenPak does not upgrade packages that are already installed. In an
existing environment, run:

```bash
python -m pip install -U urllib3
```

urllib3 2.7.0 has open advisories (two high, one medium) that are fixed in
2.8.0. A new install resolves a fixed version, because TokenPak requires
`urllib3>=2.0.0` and sets no upper limit. The Security section of the
[1.30.2 changelog entry](https://github.com/tokenpak/tokenpak/blob/v1.30.2/CHANGELOG.md)
lists the other advisory findings at this release.

## Session footer under collating locales

*Introduced in 1.30.1.*

The Claude Code footer and the Codex pane showed only `TokenPak` instead of
the session line when the shell's locale collates regex ranges, for example
`en_US.UTF-8` on Linux. TokenPak 1.30.1 fixes this. Start a new managed client
launch after upgrading so the client runs the updated footer script.

## Handoff recipient name

*Introduced in 1.30.1.*

The orchestration handoff's human recipient is now registered as `operator`.
A handoff addressed to a name that is not registered fails as an unknown agent;
address the human recipient as `operator`.

## Execution ledger recovery signal

*Introduced in 1.30.0.*

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

## Native token observations and first-session reliability

*Introduced in 1.29.0.*

Opt-in native token observations keep token measurements separate from billed
cost. They include request coverage, bounded reservations and evidence that a
response finished. Missing or incomplete observations remain unavailable; a token
count does not establish a successful task, calibrated forecast or paid savings.
See the [native token snapshot API](api-reference.md#native-token-snapshot).

Fresh companion journals record the first Claude prompt even when the external
SQLite executable is absent. Background writes no longer keep the prompt's
response pipes open. Prompt metadata does not count as completed work or provider
usage, and configured shell-hook budgets retain their refusal behavior when
SQLite is unavailable.

The companion MCP server keeps JSON-RPC on stdout and writes startup and
content-free malformed-input diagnostics to stderr. Dispatch ships an alpha CLI
and runtime with optional dependencies; station execution and delivery remain
unfinished. See the [packaged Dispatch guide](https://github.com/tokenpak/tokenpak/blob/v1.29.0/docs/guides/dispatch.md).

## Session history and recorded usage

*Introduced in 1.28.0.*

Completed Codex turns can be recovered into the local companion journal from
native history. The intake handles forked sessions and large records, preserves
existing entries, and avoids duplicate entries on replay. History listings show
the number of recorded entries. A completed turn does not establish that the
task succeeded, or supply missing provider usage.

Session economics includes an optional `recorded_usage` object. It exposes
measured token subtotals, request coverage and failed-request counts when full
session totals are unavailable. The terminal footer shows `usage N/M` for this
coverage. Any cost subtotal carries its recorded cost basis; it is not an invoice
or a complete session total. Missing usage and failed requests continue to affect
the full-session totals, guard and forecast inputs.

Explicit `xhigh` effort is a separate forecast cell when its recorded provenance
supports that value. It does not borrow histories from unknown effort. Forecasts
still require eligible histories and scored coverage; sparse cells remain
learning or unavailable. See [terminal forecasts](companion-session-forecast.md).

## Install and verify

1. Retain the previous package pair and environment for rollback.
2. If you do not use Pro, install `tokenpak==1.30.2` with the extras already
   used by your installation. The standard service profile is
   `tokenpak[serve,tokens,telemetry]==1.30.2`.
3. If you use Pro, do not install OSS 1.30.2. Pro 0.5.2 supports OSS 1.26.0
   through 1.30.1 with TIP-1.0 and refuses 1.30.2. Pro 0.5.1 supports OSS only
   through 1.30.0 — if you stay on Pro 0.5.1, stay on OSS 1.30.0 as well. Keep
   the pair you have until a Pro release that supports 1.30.2 is published, then
   upgrade OSS and Pro together through your existing licensed delivery channel.
   pip does not stop an OSS-only upgrade: `pip install --upgrade tokenpak`
   installs 1.30.2 next to Pro 0.5.2, prints a dependency-conflict message, and
   `pip check` then fails. If that happens, reinstall `tokenpak==1.30.1`.
4. After active requests finish, restart the services that use the replaced
   environment. Reinstall or repoint configured companion hooks when changing
   environment paths. Preserve explicit journal-root settings and verify the
   hooks and service read the intended existing journal.
5. Run `tokenpak --version`, `tokenpak doctor`, and
   `tokenpak status --json --session ID` for a session you intend to inspect.
   Start a new managed client launch to use updated hooks and display code.

This is a package-only upgrade: no database migration and no configuration
change are required. A license write now also creates an empty
`license.json.lock` file beside `license.json`. If you upgrade from 1.29.0 or
earlier, TokenPak creates a new `execution_ledger.db` in its state directory
the first time it starts; existing state and configured journal locations are
otherwise unaffected.

## Roll back

Reinstall OSS 1.30.1. TokenPak 1.30.2 adds no database state, so nothing needs
to be removed, and 1.30.1 ignores the empty `license.json.lock` file that a
license write leaves beside `license.json`. Rolling back removes the license
fixes described above; it does not undo licenses issued or revoked in the
meantime. If you run Pro, keep Pro 0.5.2, which supports OSS 1.30.1. Rolling
back further, to 1.30.0, pairs with either Pro 0.5.1 or Pro 0.5.2, and rolling
back to 1.29.0 leaves the `execution_ledger.db` file in place; 1.29.0 serves
normally with it present. Restore the previous environment pointer and hook
configuration after active requests finish. Published artifacts and tags are
never overwritten.

## Limits and dependency findings

A `terminally_failed` or `recovery_status` signal on a retried request means
the execution ledger detected a proxy restart mid-stream. It is not
transparent replay and not a full exactly-once resume: the original in-flight
call is not silently completed or resumed for you. See
[known limitations](KNOWN_LIMITATIONS.md#execution-ledger-recovery-is-fail-with-signal-not-replay)
before treating a recovery signal as a completed retry.

Optional dependency findings are documented in
[SECURITY.md](https://github.com/tokenpak/tokenpak/blob/v1.30.2/SECURITY.md).
Release validation covers changed behavior, installed artifacts, upgrade and
rollback of OSS 1.30.2. It does not cover a Pro pairing, because no Pro release
supports 1.30.2 yet. Publication, deployment and the observation period remain
separate milestones.
