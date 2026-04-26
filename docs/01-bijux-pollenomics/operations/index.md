---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Operations

Use this section when the question is procedural: how to set up the runtime,
which command path to run, how to separate safe inspection from state-changing
rebuild work, and how to recover when the evidence pipeline produces unexpected
results.

This package is operationally sensitive because its outputs are checked into the
repository and published on the docs site. A sloppy rerun can widen the review
surface across `data/` and `docs/report/`, so the runtime needs clear,
repeatable procedures rather than vague “just rerun it” habits.

```mermaid
flowchart LR
    setup["bootstrap the runtime environment"]
    inspect["inspect commands and inputs safely"]
    rebuild["run controlled rebuild workflows"]
    diagnose["diagnose output or source failures"]
    release["prepare reviewed publication changes"]
    reader["reader question<br/>which procedure protects the tracked outputs?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class rebuild,page reader;
    class setup,inspect,release positive;
    class diagnose caution;
    setup --> reader
    inspect --> reader
    rebuild --> reader
    diagnose --> reader
    release --> reader
```

## Start Here

- open [Installation and Setup](installation-and-setup.md) for environment and
  bootstrap expectations
- open [Common Workflows](common-workflows.md) for the main rebuild and verify
  paths
- open [Failure Recovery](failure-recovery.md) or
  [Observability and Diagnostics](observability-and-diagnostics.md) when a run
  has already diverged from the expected outputs
- open [Release and Versioning](release-and-versioning.md) when the question is
  about tags, package artifacts, or release evidence

## Pages In This Section

- [Installation and Setup](installation-and-setup.md)
- [Local Development](local-development.md)
- [Common Workflows](common-workflows.md)
- [Observability and Diagnostics](observability-and-diagnostics.md)
- [Performance and Scaling](performance-and-scaling.md)
- [Failure Recovery](failure-recovery.md)
- [Release and Versioning](release-and-versioning.md)
- [Security and Safety](security-and-safety.md)
- [Deployment Boundaries](deployment-boundaries.md)

## Use This Section When

- you need a repeatable procedure for collecting, reporting, or publishing
- you need to minimize review noise while still regenerating evidence
- a failure needs diagnosis without guessing which layer owns the repair

## Do Not Use This Section When

- the real question is which package or module owns a behavior
- you are still deciding whether a command or file layout counts as a contract
- the issue is primarily about proof, review coverage, or unresolved risk

## Read Across The Package

- open [Foundation](../foundation/index.md) when an operational question is
  really about whether the runtime should own the behavior at all
- open [Architecture](../architecture/index.md) when recovery depends on
  understanding dispatch, collection, or reporting structure
- open [Interfaces](../interfaces/index.md) when a procedure may change CLI,
  config, tracked data, or published artifact contracts
- open [Quality](../quality/index.md) when the real question is what evidence
  should be gathered before or after a rerun

## Reader Takeaway

Use `Operations` to keep runtime work controlled, reviewable, and recoverable.
If a procedure cannot explain how it protects tracked evidence outputs, it is
not yet an operational practice this repository should rely on.

## Purpose

This page introduces the operational handbook for `bijux-pollenomics` and
routes readers to the procedures that govern setup, rebuilds, diagnostics, and
publication work.
