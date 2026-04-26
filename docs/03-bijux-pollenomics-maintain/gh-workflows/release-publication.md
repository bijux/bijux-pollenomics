---
title: release-publication
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-19
---

# release-publication

Tagged publication is split across dedicated workflows:
`release-pypi.yml`, `release-ghcr.yml`, and `release-github.yml`.

Each release workflow reads `.github/release.env` and calls
`release-artifacts.yml` to build staged package artifacts for
`bijux-pollenomics` and `pollenomics`.

Release workflows run for version tags and manual dispatch. Publication stays
package-scoped so PyPI uploads and GHCR bundle publication can run in parallel,
while GitHub release assembly uses the same staged assets.

## Current Job Tree

- `release-artifacts.yml` builds staged package release assets
- `release-pypi.yml` publishes staged distributions to PyPI
- `release-ghcr.yml` publishes staged release bundles to GHCR as OCI artifacts
- `release-github.yml` creates the GitHub release and uploads staged assets

## Purpose

This page shows the split release workflow topology and where each publication
target is owned.
