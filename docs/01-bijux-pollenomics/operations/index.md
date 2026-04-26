---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Operations

Open this section when the question is procedural: how to set up the runtime,
which command path to run, how to separate safe inspection from state-changing
rebuild work, and how to recover when the evidence pipeline produces
unexpected results.

This package is operationally sensitive because its outputs are checked into the
repository and published on the docs site. A sloppy rerun can widen the review
surface across `data/` and `docs/report/`, so the runtime needs clear,
repeatable procedures rather than vague “just rerun it” habits.

That is why this section matters even for readers who are not writing code.
When a rebuild changes visible evidence, the procedure is part of the
credibility story: which command was run, which files were expected to move,
and which review surface must be inspected before the change is trusted.

## Start Here

- open [Installation and Setup](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/installation-and-setup/) for environment and
  bootstrap expectations
- open [Common Workflows](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/common-workflows/) for the main rebuild and verify
  paths
- open [Failure Recovery](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/failure-recovery/) or
  [Observability and Diagnostics](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/observability-and-diagnostics/) when a run
  has already diverged from the expected outputs
- open [Release and Versioning](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/release-and-versioning/) when the question is
  about tags, package artifacts, or release evidence
- open [Deployment Boundaries](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/deployment-boundaries/) before treating this
  package like a long-running service or hidden background system

## Pages In This Section

- [Installation and Setup](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/common-workflows/)
- [Observability and Diagnostics](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/performance-and-scaling/)
- [Failure Recovery](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/failure-recovery/)
- [Release and Versioning](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/security-and-safety/)
- [Deployment Boundaries](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/deployment-boundaries/)

## Open This Section When

- you need a repeatable procedure for collecting, reporting, or publishing
- you need to minimize review noise while still regenerating evidence
- a failure needs diagnosis without guessing which layer owns the repair

## Open Another Section When

- the real question is which package or module owns a behavior
- you are still deciding whether a command or file layout counts as a contract
- the issue is primarily about proof, review coverage, or unresolved risk

## What This Section Covers

- which operational path is safe for inspection versus state-changing rebuild
  work
- which commands widen the tracked review surface across `data/` and
  `docs/report/`
- which failure should send a reader into runtime diagnostics rather than into
  provenance or automation docs

## Concrete Anchors

- `src/bijux_pollenomics/command_line/runtime/handlers.py` for the operational
  entrypoints that trigger collection and reporting work
- `src/bijux_pollenomics/data_downloader/pipeline/staging.py` and
  `src/bijux_pollenomics/data_downloader/pipeline/summary_writer.py` for
  controlled rewrite behavior
- `src/bijux_pollenomics/reporting/bundles/staging.py` and
  `src/bijux_pollenomics/reporting/bundles/published_reports.py` for
  publication-facing output generation
- `tests/regression/test_data_collector.py` and
  `tests/regression/test_country_report.py` for the narrowest operational
  backstops that defend reruns

## Across This Package

- open [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/) when an operational question is
  really about whether the runtime should own the behavior at all
- open [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when recovery depends on
  understanding dispatch, collection, or reporting structure
- open [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/) when a procedure may change CLI,
  config, tracked data, or published artifact contracts
- open [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) when the real question is what evidence
  should be gathered before or after a rerun

## Bottom Line

Open this section to keep runtime work controlled, reviewable, and
recoverable. If a procedure cannot explain how it protects tracked evidence
outputs, it is not yet an operational practice this repository should rely on.
