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

Use it when the question is which root command to run, which target rewrites
tracked state, or how package-level makefiles are routed from the repository
entrypoints.

```mermaid
flowchart LR
    root["root make target"]
    dispatch["package dispatch"]
    ci["CI targets"]
    release["release targets"]
    env["environment model"]
    authoring["authoring rules"]
    reader["reader question<br/>which command surface owns this action?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class root,page reader;
    class dispatch,ci,release,env,authoring positive;
    root --> dispatch
    root --> ci
    root --> release
    root --> env
    root --> authoring
    root --> reader
```

## Start Here

- open [Root Entrypoints](root-entrypoints.md) for the top-level command surface
- open [CI Targets](ci-targets.md) when the question is about verification and
  automation contracts
- open [Release Surfaces](release-surfaces.md) when the question is about
  publication-related make targets

## Pages In This Section

- [Make System Overview](make-system-overview.md)
- [Repository Layout](repository-layout.md)
- [Root Entrypoints](root-entrypoints.md)
- [Package Dispatch](package-dispatch.md)
- [Package Contracts](package-contracts.md)
- [Release Surfaces](release-surfaces.md)
- [CI Targets](ci-targets.md)
- [Environment Model](environment-model.md)
- [Authoring Rules](authoring-rules.md)

## Use This Section When

- you need to know which repository command starts a verification, build,
  release, or docs task
- a package target appears to be invoked indirectly from a root-level Make
  entrypoint
- the question is about command contracts, shared variables, or how maintainers
  are expected to add new targets safely

## Do Not Use This Section When

- the real issue is inside package implementation, data semantics, or atlas
  publication behavior
- the question is about GitHub Actions triggers rather than local or CI command
  routing
- you are looking for reader-facing product behavior instead of maintainer
  command surfaces

## Reader Takeaway

Use `makes/` to understand the repository command contract: what a maintainer
runs, which shared target fans out into package work, and where command
behavior is intentionally centralized. Move to `gh-workflows/` when the real
question is automation triggers rather than Make routing.

## Purpose

This page organizes the repository Make-system documentation so maintainers can
trace a command from the root surface to the package or CI behavior it invokes.
