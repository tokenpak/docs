---
title: Upgrade TokenPak
rung: 2
audience: Developers upgrading an existing TokenPak installation.
updated: 2026-09-22
status: current
---

# Upgrade to TokenPak 1.29.0

This guide is for developers upgrading from TokenPak 1.28.0. The compatible
published pair is OSS 1.29.0 and the separately distributed Pro 0.5.0.

## Native token observations and first-session reliability

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

1. Back up configuration and use consistent backups for SQLite state. Retain the
   previous package pair and environment for rollback.
2. Install `tokenpak==1.29.0` with the extras already used by your installation.
   The standard service profile is `tokenpak[serve,tokens,telemetry]==1.29.0`.
3. If you use Pro, install Pro 0.5.0 through your existing licensed delivery
   channel. Its supported OSS range is 1.26.0 through 1.29.0 with TIP-1.0.
   Native token measurement requires OSS 1.29.0. Pro 0.4.3 supports OSS only
   through 1.28.0, so upgrade the packages together.
4. After active requests finish, restart the services that use the replaced
   environment. Reinstall or repoint configured companion hooks when changing
   environment paths. Preserve explicit journal-root settings and verify the
   hooks and service read the intended existing journal.
5. Run `tokenpak --version`, `tokenpak doctor`, and
   `tokenpak status --json --session ID` for a session you intend to inspect.
   Start a new managed client launch to use updated hooks and display code.

Database migrations are additive and one-way. They preserve historical rows and
priced reservation domains without relabeling them as measured native tokens.
This release does not enable automatic rerouting or require deleting sessions.
Existing clients may retain older modules until they exit.

## Roll back

Restore OSS 1.28.0 and Pro 0.4.3 together with the pre-upgrade database backup.
Preserve a separate copy of post-upgrade state before restoring that backup;
never overwrite newer evidence without retaining it. Do not try to reverse the
schema migration in place. Restore the previous environment pointer and hook
configuration after active requests finish. Published artifacts and tags are
never overwritten.

## Limits and dependency findings

Recovered journal entries are metadata about recorded turns, not accepted task
outcomes or admitted Reroute priors. Recorded-usage subtotals do not make an
incomplete or mixed session eligible for forecasting. Human comprehension and
realized reroute savings require their own evidence.

Optional dependency findings are documented in
[SECURITY.md](https://github.com/tokenpak/tokenpak/blob/v1.29.0/SECURITY.md).
Release validation covers changed behavior, installed artifacts, paired
compatibility, upgrade and rollback. Publication, deployment and the observation
period remain separate milestones.
