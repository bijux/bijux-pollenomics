---
title: Release Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Release Surfaces

The make system exposes release-facing surfaces for package build, SBOM,
package verification, docs publication preparation, and API freeze support.
`makes/publish.mk` now declares the repository-owned version resolver and
publication guard modules that keep tag-derived versions aligned with staged
artifacts.

