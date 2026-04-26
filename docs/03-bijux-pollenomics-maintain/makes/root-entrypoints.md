---
title: Root Entrypoints
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Root Entrypoints

The root entrypoint is intentionally small: `Makefile` includes `makes/root.mk`.

## Stable Repository Commands

- `check` runs the full repository verification flow
- `data-prep` refreshes tracked source data under `data/`
- `reports` refreshes tracked report outputs under `docs/report/`
- `app-state` rebuilds tracked data, reports, and docs
- `sync-badges` and `sync-license-assets` run repository-owned maintainer sync
  helpers
