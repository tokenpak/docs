---
title: TokenPak demo data
rung: 2
audience: Developers who want sample events in the local dashboard before real traffic exists.
updated: 2026-10-06
status: current
---

# TokenPak demo data

This page is for developers who want sample events in the local dashboard before real traffic exists. `tokenpak demo --seed` writes randomly generated sample events, each marked `is_demo`. The values are illustrative; they are not a measurement of your savings.

## Seed demo data

```bash
tokenpak demo --seed
```

Writes 500 sample events spread over 24 hours, using a mix of Claude and GPT model names with random token counts, cache values and latencies.

To change the size or the time window:

```bash
tokenpak demo --seed --seed-count 1000 --seed-hours 12   # 1000 events over 12 hours
```

## Clear demo data

```bash
tokenpak demo --clear
```

Removes the events marked `is_demo` and keeps every other event.

## Where the sample events go

Sample events are appended to the same local compression event log that the proxy writes and the dashboard reads, so they sit next to real events until you clear them. Seeding again adds another batch. Run `tokenpak demo --clear` before you look at real traffic.

## Offline fixture demo

`tokenpak demo` with no flags prints an offline comparison on a built-in sample fixture. Its output is labelled "not a savings receipt".
