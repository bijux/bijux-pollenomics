---
title: Operational Boundaries
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Operational Boundaries

Operations guidance should make two boundaries obvious: what a maintainer can
do locally with confidence, and what the runtime still refuses to claim.

## Local Development

- start with `make install`
- use `make docs-serve` for docs review
- prefer narrow tests before broad rebuilds

## Observability And Diagnostics

- inspect `data/collection_summary.json` after collection work
- inspect `docs/report/published_reports_summary.json` after publication work
- inspect repository truth reviews when a change affects scope or claim posture

## Release And Versioning

- the runtime follows the checked-in AADR version and report naming contracts
- release automation publishes only after repository-health checks pass
- package and report publication are downstream of tracked repository state

## Security And Safety

- keep transient output under `artifacts/`
- do not treat unchecked external source output as publishable state
- do not let public docs or atlas language outrun the tracked evidence surfaces

## Performance Posture

Rebuilds can be slow because they touch tracked source and report surfaces.
That cost is acceptable when it preserves reviewable repository truth.
