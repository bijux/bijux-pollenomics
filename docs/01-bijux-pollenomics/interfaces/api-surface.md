---
title: API Surface
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# API Surface

The runtime's stable public surface is intentionally smaller than its internal
module tree. The default public entrypoint is the CLI, but some Python import
surfaces are still durable enough to treat as repository contracts.

## Stable Reader-Facing Surfaces

- the `bijux-pollenomics` and `pollenomics` console scripts
- checked publication outputs under `docs/report/`
- tracked data outputs under `data/`
- the frozen public API contract under `apis/bijux-pollenomics/v1/`

## Python Surface

Treat these as durable repository-owned import boundaries:

- `bijux_pollenomics.config`
- `bijux_pollenomics.command_line`
- `bijux_pollenomics.reporting`
- `bijux_pollenomics.data_downloader.contracts`

Everything deeper than those boundaries can change as implementation detail so
long as command and file contracts stay stable.

## Compatibility Posture

- compatibility is primarily file-contract and CLI-contract compatibility
- internal helper layout can move when the public contracts remain reviewable
- aliases under the `pollenomics` package must preserve the same runtime
  behavior, not invent a different product story
