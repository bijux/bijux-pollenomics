---
title: API Surface
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# API Surface

The stable public API of this repository is deliberately small. Most readers
should treat the CLI and checked-in files as the main public surface. Only a
small set of Python import paths are stable enough to depend on directly.

That restraint is intentional. A public API page should tell the reader what is
safe to rely on, not quietly imply that every internal module is part of the
promise.

## The Main Public Surfaces

- the `bijux-pollenomics` and `pollenomics` console scripts
- checked publication outputs under `docs/report/`
- tracked data outputs under `data/`
- the frozen public API contract under `apis/bijux-pollenomics/v1/`

For most users, that is enough. The CLI and the checked-in public outputs are
the intended day-to-day contract.

## Stable Python Surface

Treat these as durable repository-owned import boundaries:

- `bijux_pollenomics.config`
- `bijux_pollenomics.command_line`
- `bijux_pollenomics.reporting`
- `bijux_pollenomics.data_downloader.contracts`

Everything deeper than those boundaries can change as implementation detail so
long as command and file contracts stay stable.

## What This Means In Practice

- import from these named boundaries only if you need Python integration
- expect deeper helpers and submodules to move when the implementation improves
- prefer CLI and file contracts when the same task can be done either way

## Compatibility Posture

- compatibility is primarily file-contract and CLI-contract compatibility
- internal helper layout can move when the public contracts remain reviewable
- aliases under the `pollenomics` package must preserve the same runtime
  behavior, not invent a different product story

## Practical Reading Rule

If you are unsure whether a Python import is public, assume it is not unless it
is named here or frozen under `apis/bijux-pollenomics/v1/`. The repository
prefers a small honest contract to a large unstable one.
