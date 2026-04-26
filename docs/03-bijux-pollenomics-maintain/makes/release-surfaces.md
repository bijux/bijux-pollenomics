---
title: Release Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Release Surfaces

The make system exposes release-facing targets for package build, verification,
SBOM generation, docs preparation, and API freeze support.

## Current Anchors

- `package-check`, `package-smoke`, and `package-source-smoke`
- `package-verify` as the packaging proof surface
- `makes/publish.mk` for version resolution and publication guard wiring
