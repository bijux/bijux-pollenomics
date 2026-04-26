---
title: release-publication
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# release-publication

Tagged publication is split across dedicated workflows.

## Current Job Tree

- `release-artifacts.yml` builds staged package artifacts
- `release-pypi.yml` publishes Python distributions
- `release-ghcr.yml` publishes release bundles to GHCR
- `release-github.yml` assembles the GitHub release and uploads staged assets

## Boundary

Release publication is intentionally split by destination. That keeps package
artifacts, OCI bundles, and GitHub release assembly inspectable instead of
hiding all publication logic in one job.
