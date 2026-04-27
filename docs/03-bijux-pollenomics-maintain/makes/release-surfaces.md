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

## Release Surface Model

```mermaid
flowchart TB
    prep["release-facing make targets"]
    verify["package verification and smoke checks"]
    artifacts["build, sbom, docs, api artifacts"]
    publish["publish wiring in makes/publish.mk"]

    prep --> verify
    prep --> artifacts
    verify --> publish
    artifacts --> publish
```

This page should make release surfaces feel like a staged proof path. Release
targets are valuable because they keep verification, artifact preparation, and
publish wiring visible before anything reaches a public destination.

## Current Anchors

- `package-check`, `package-smoke`, and `package-source-smoke`
- `package-verify` as the packaging proof surface
- `makes/publish.mk` for version resolution and publication guard wiring

## Design Pressure

The easy failure is to see release targets as just packaging shortcuts, which
hides how they bundle together proof, artifact preparation, and publish
eligibility.
