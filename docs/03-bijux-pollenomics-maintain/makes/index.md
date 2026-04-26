---
title: makes
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# makes

This section documents the repository make system.

Open it when the question is which root command to run, which target rewrites
tracked state, or how package-level makefiles are routed from the repository
entrypoints.

The make system matters because it is the shortest path from intent to
repository-wide consequences. This section shows which target is safe for
inspection, which one rewrites `data/` or `docs/report/`, and which one is
only a dispatch layer for package-specific work.

## Start Here

- open [Root Entrypoints](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/root-entrypoints/) for the top-level command surface
- open [CI Targets](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/ci-targets/) when the question is about verification and
  automation contracts
- open [Release Surfaces](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/release-surfaces/) when the question is about
  publication-related make targets

## Pages In This Section

- [Make System Overview](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/make-system-overview/)
- [Repository Layout](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/repository-layout/)
- [Root Entrypoints](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/root-entrypoints/)
- [Package Dispatch](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/package-dispatch/)
- [Package Contracts](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/package-contracts/)
- [Release Surfaces](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/release-surfaces/)
- [CI Targets](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/ci-targets/)
- [Environment Model](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/environment-model/)
- [Authoring Rules](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/makes/authoring-rules/)

## Open This Section When

- you need to know which repository command starts a verification, build,
  release, or docs task
- a package target appears to be invoked indirectly from a root-level Make
  entrypoint
- the question is about command contracts, shared variables, or how maintainers
  are expected to add new targets safely

## Open Another Section When

- the real issue is inside package implementation, data semantics, or atlas
  publication behavior
- the question is about GitHub Actions triggers rather than local or CI command
  routing
- you are looking for reader-facing product behavior instead of maintainer
  command surfaces

## What This Section Clarifies

- which repository targets are top-level commands versus package dispatch
  surfaces
- which command paths widen the tracked review surface by rewriting runtime
  outputs
- where release and publication routing stop being local Make concerns and turn
  into broader workflow automation concerns

## Concrete Anchors

- `makes/root.mk` for the top-level `check`, `data-prep`, `reports`, and
  `app-state` command surfaces
- `makes/packages.mk` for package catalog and dispatch ownership
- `makes/publish.mk` for shared publication-routing rules
- `makes/packages/bijux-pollenomics.mk` and
  `makes/packages/bijux-pollenomics-dev.mk` for package-specific command
  profiles

## Bottom Line

Open `makes/` to understand the repository command contract: what a maintainer
runs, which shared target fans out into package work, and where command
behavior is intentionally centralized. Open `gh-workflows/` when the real
question is automation triggers rather than Make routing.
