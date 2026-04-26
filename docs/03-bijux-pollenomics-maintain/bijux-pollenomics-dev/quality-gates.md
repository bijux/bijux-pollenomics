---
title: Quality Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Quality Gates

`bijux-pollenomics-dev` supports repository quality by turning review rules into
executable checks.

## Current Gates

- `api/freeze_contracts.py` keeps checked-in pinned API artifacts aligned with
  schema files
- `quality/deptry_scan.py` applies repository dependency policy to package
  scans
- `docs/badge_sync.py` keeps managed badge blocks synchronized where required
- `release/license_assets.py` keeps package license assets aligned with root
  sources
