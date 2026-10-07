---
title: Upgrade TokenPak
rung: 2
audience: Developers upgrading an existing TokenPak installation.
updated: 2026-10-07
status: current
---

# Upgrade to TokenPak 1.30.3

This guide is for developers upgrading from TokenPak 1.30.2. The compatible
published pair is OSS 1.30.3 and the separately distributed Pro 0.6.0, which
requires exactly OSS 1.30.3. Pro 0.5.x supports OSS only through 1.30.1, so if
you use Pro, read [Pairing with Pro 0.6.0](#pairing-with-pro-060) first and
upgrade both packages together. If you do not use Pro, upgrade as described in
[Install and verify](#install-and-verify). If you are upgrading from an earlier
release, also read the 1.30.2, 1.30.1, 1.30.0, 1.29.0 and 1.28.0 changes below.

## License lookup in the older home folder

TokenPak keeps its files in `~/.tpk`, or in `~/.tokenpak` on an installation
that predates it. Before 1.30.3 it chose one of the two folders for everything,
by what that folder held. If your `license.json` sat in `~/.tokenpak` while
`~/.tpk` held other files, such as companion data or logs, the installation read
as unlicensed: `tokenpak license` and `tokenpak features` showed the free plan,
and `tokenpak activate` would have stored a new pending key in `~/.tpk` next to
the installed license.

TokenPak 1.30.3 looks up the license file on its own:

| Setting | License file used |
|---|---|
| `TOKENPAK_LICENSE_FILE` set | That file |
| `TOKENPAK_HOME` set | `<TOKENPAK_HOME>/license.json` only; the default folders are never consulted |
| Neither set, `~/.tpk/license.json` exists | `~/.tpk/license.json` |
| Neither set, only `~/.tokenpak/license.json` exists | `~/.tokenpak/license.json` |
| Neither set, no license in either folder | A read uses the selected home; a first license is written to the home a new installation uses |

If both default folders hold a license file, the one in `~/.tpk` is used. The
check is for a file, not for a valid license. Every other file, including the
Pro daemon connection file (`pro/daemon.sock-info`), stays in the selected home.
TokenPak moves and copies nothing, and `license.json` keeps its format.

## Activation, refresh and removal follow the file in use

Activating, refreshing and removing a license act on the file that was found, so
a read and the write that follows name the same file. The `license.json.lock`
file is created beside it. `tokenpak activate` still refuses to replace an
installed, current signed license, now including one in the other folder.
Activating the key that is already installed still reports that it is already
active, and a pending license is replaced in place.

If you ran `tokenpak activate` on 1.30.2 while your license sat in `~/.tokenpak`
and `~/.tpk` held other files, 1.30.2 stored a pending key in
`~/.tpk/license.json`. That file now takes precedence over the license in
`~/.tokenpak`. Run `tokenpak deactivate`: it removes the file in use, and the
license in `~/.tokenpak` then takes effect.

## A refused request releases its hold first

When the token guard refuses a request locally, that request has already
reserved its spend hold and, with the circuit half open, taken the single
provider probe. Before 1.30.3 the proxy wrote the 402 refusal first and released
both afterwards. A client that retried as soon as it read the refusal could
reach admission while the earlier request's unsent hold was still active, and
was refused again with `tokenpak_spend_guard_reservation_blocked`. TokenPak
1.30.3 releases the hold and the probe before it sends the refusal, so a retry
made as soon as the client reads the refusal is no longer blocked by that
request's own hold.

Spend enforcement is unchanged: a request that was sent keeps its hold until
usage is recorded, and a refused request consumes nothing.

## Recipe count in help text

The package has shipped 57 built-in compression recipes since 1.18.0. The
`tokenpak demo --list` help still said 50, the count before 1.18.0, and now says
57. The `--category` help for `tokenpak demo` and `tokenpak recipe list` now
names all eight categories, including `go` and `rust`. The recipes themselves
are unchanged.

## Dependencies in existing environments

Upgrading TokenPak does not upgrade packages that are already installed. In an
existing environment, run:

```bash
python -m pip install -U urllib3
```

urllib3 2.7.0 has open advisories (two high, one medium) that are fixed in
2.8.0. A new install resolves a fixed version, because TokenPak requires
`urllib3>=2.0.0` and sets no upper limit. TokenPak 1.30.3 also moves its
development locks to fixed versions of urllib3, multidict, Werkzeug and LiteLLM;
those advisories affected only the locks. If you installed the
`integrations-litellm` extra, upgrade `litellm` too. The Security section of the
[1.30.3 changelog entry](https://github.com/tokenpak/tokenpak/blob/v1.30.3/CHANGELOG.md)
lists the other advisory findings at this release.

## Pairing with Pro 0.6.0

Pro is a separate licensed package. There is no self-service purchase; write to
hello@tokenpak.ai about access.

Pro 0.6.0 requires exactly OSS 1.30.3. It declares 1.30.3 as both its minimum
and its maximum supported OSS version, with TIP-1.0 unchanged. Pro 0.5.x
supports OSS only through 1.30.1, so it does not pair with OSS 1.30.3. If you
use Pro 0.5.x, stay on the OSS version it supports, 1.30.1 for Pro 0.5.2 and
1.30.0 for Pro 0.5.1, until you upgrade both packages together in one pip
command.

Pro 0.6.0 also changes how Pro reads your license:

- It verifies the issuer's signature on the license file before Pro features turn
  on. An unsigned or edited license runs as the open-source edition.
- It finds the license in either home folder, as OSS 1.30.3 does.
- Its offline limit applies only to licenses whose issuer asks for periodic
  checks.

The [1.30.3 release log](https://github.com/tokenpak/tokenpak/blob/v1.30.3/docs/release-log/v1.30.3.md)
describes the paired upgrade step by step, including a gate script in the source
tree that checks the installed pair before you switch to it.

## License activation keeps an installed license

*Introduced in 1.30.2.*

`tokenpak activate` no longer replaces a license that is installed and still
current. Activating a different key leaves `license.json` unchanged and names
`tokenpak deactivate` as the way to replace the license. Activating the key
that is already installed reports that it is already active. An expired or
pending license can still be replaced by activating a new key.

## Expired licenses read as expired

*Introduced in 1.30.2.*

`tokenpak license` and `tokenpak features` honor the license's `expires_at`
date and the issuer's `grace_days`. A lapsed license reads as expired and no
longer grants Pro through its tier. A license whose `expires_at` cannot be read
counts as expired.

## License writes and the Pro daemon connection file

*Introduced in 1.30.2.*

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

*Introduced in 1.30.2.*

The package summary that PyPI and `pip show tokenpak` display, and
`tokenpak.__description__`, no longer claim automatic cost cuts or default
compression and routing. They now read: "Local proxy for coding agents that
records each request and shows how far the session can go: measured usage,
estimated cost, burn and runway."

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
2. If you do not use Pro, install `tokenpak==1.30.3` with the extras already
   used by your installation. The standard service profile is
   `tokenpak[serve,tokens,telemetry]==1.30.3`.
3. If you use Pro, upgrade OSS and Pro together, in one `pip install` command
   that names OSS 1.30.3 and Pro 0.6.0, through your existing licensed delivery
   channel. Pro 0.6.0 requires exactly OSS 1.30.3. Do not upgrade OSS alone: Pro
   0.5.2 supports OSS 1.26.0 through 1.30.1 with TIP-1.0, and Pro 0.5.1 supports
   OSS only through 1.30.0. pip does not stop an OSS-only upgrade:
   `pip install --upgrade tokenpak` installs 1.30.3 next to Pro 0.5.2, prints a
   dependency-conflict message, and `pip check` then fails. If that happens,
   reinstall `tokenpak==1.30.1`. If you are not ready to upgrade both packages,
   keep the pair you have. After the paired upgrade, run `python -m pip check`;
   it must report no broken requirements.
4. After active requests finish, restart the services that use the replaced
   environment. Reinstall or repoint configured companion hooks when changing
   environment paths. Preserve explicit journal-root settings and verify the
   hooks and service read the intended existing journal.
5. Run `tokenpak --version`, `tokenpak doctor`, and
   `tokenpak status --json --session ID` for a session you intend to inspect.
   Start a new managed client launch to use updated hooks and display code.

This is a package-only upgrade: no database migration, configuration change or
data backup is required, and no file is moved. Since 1.30.2, a license write
also creates an empty `license.json.lock` file beside the license file in use.
If you upgrade from 1.29.0 or earlier, TokenPak creates a new
`execution_ledger.db` in its state directory the first time it starts; existing
state and configured journal locations are otherwise unaffected.

## Roll back

Reinstall OSS 1.30.2, or 1.30.1. TokenPak 1.30.3 adds no database state and
moves no file, so nothing needs to be removed, and 1.30.1 ignores the empty
`license.json.lock` file that a license write leaves beside the license file.
Rolling back restores the old license lookup, so an installation whose license
sits in `~/.tokenpak` while `~/.tpk` holds other files reads as the free plan
again, and the false `tokenpak_spend_guard_reservation_blocked` refusal on an
immediate retry can return. Rolling back does not undo licenses issued or
revoked in the meantime.

If you run Pro, switch back to the previous environment, or reinstall the
previous pair, OSS 1.30.1 with Pro 0.5.2, in one `pip install` command. Never
downgrade only one of the two packages. Rolling back further, to 1.30.0, pairs
with either Pro 0.5.1 or Pro 0.5.2, and rolling back to 1.29.0 leaves the
`execution_ledger.db` file in place; 1.29.0 serves normally with it present.
Restore the previous environment pointer and hook configuration after active
requests finish. Published artifacts and tags are never overwritten.

## Limits and dependency findings

A `terminally_failed` or `recovery_status` signal on a retried request means
the execution ledger detected a proxy restart mid-stream. It is not
transparent replay and not a full exactly-once resume: the original in-flight
call is not silently completed or resumed for you. See
[known limitations](KNOWN_LIMITATIONS.md#execution-ledger-recovery-is-fail-with-signal-not-replay)
before treating a recovery signal as a completed retry.

Optional dependency findings are documented in
[SECURITY.md](https://github.com/tokenpak/tokenpak/blob/v1.30.3/SECURITY.md).
Release validation of OSS 1.30.3 covers changed behavior, installed artifacts,
upgrade and rollback of the OSS package. It did not install Pro, so it does not
cover the OSS and Pro pair.
