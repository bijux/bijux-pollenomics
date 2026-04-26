---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Architecture

Use this section when the important question is how the runtime is put
together: where command dispatch begins, where evidence collection branches by
source family, and where report building turns tracked files into visible atlas
and country outputs.

This package only becomes trustworthy when a reader can follow the actual
structural path from CLI to collector to report bundle without guessing. The
goal here is not to list modules mechanically, but to make the execution seams
and rewrite boundaries easy to see.

That structural story is narrower than a generic application architecture
diagram. The key reader question is where the repository chooses behavior:
where commands are interpreted, where source families branch, where tracked
files are rewritten, and where visible publication assets are assembled.

```mermaid
flowchart LR
    reader["reader question<br/>where does runtime behavior actually live?"]
    cli["cli.py and command_line/<br/>parse commands and select work"]
    collection["data_downloader/<br/>collect, stage, normalize<br/>by source family"]
    reporting["reporting/<br/>assemble country bundles<br/>and atlas output"]
    tracked["tracked rewrite surfaces<br/>data/ and docs/report/"]
    proof["tests and repository contracts<br/>check the structural promises"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class reader page;
    class cli,collection,reporting,tracked positive;
    class proof positive;
    reader --> cli
    cli --> collection
    cli --> reporting
    collection --> tracked
    reporting --> tracked
    tracked --> proof
```

## Start Here

- open [Module Map](module-map.md) for the shortest code-level tour
- open [Execution Model](execution-model.md) when you need to trace the full
  command-to-output path
- open [Integration Seams](integration-seams.md) when the handoff between CLI,
  collection, and reporting is the real question
- open [State and Persistence](state-and-persistence.md) when tracked output
  rewrites and staging boundaries are the hard part

## Pages In This Section

- [Module Map](module-map.md)
- [Dependency Direction](dependency-direction.md)
- [Execution Model](execution-model.md)
- [State and Persistence](state-and-persistence.md)
- [Integration Seams](integration-seams.md)
- [Error Model](error-model.md)
- [Extensibility Model](extensibility-model.md)
- [Code Navigation](code-navigation.md)
- [Architecture Risks](architecture-risks.md)

## Use This Section When

- you need to trace structural ownership before refactoring the runtime
- you are checking where output-writing logic actually lives
- you need to understand how command dispatch, source collection, and report
  building stay separated

## Do Not Use This Section When

- the question is mainly about public command syntax, file contracts, or
  defaults
- the issue is operational, such as rebuild workflow or release handling
- you need proof, risk posture, or validation criteria more than structural
  flow

## What This Section Clarifies

- where command parsing ends and source-specific collection logic begins
- where data normalization hands off to publication assembly
- where tracked repository rewrites happen, and therefore where structural
  mistakes create visible review noise first

## Concrete Anchors

- `src/bijux_pollenomics/command_line/parsing/` and
  `src/bijux_pollenomics/command_line/runtime/` for CLI parsing and dispatch
- `src/bijux_pollenomics/data_downloader/pipeline/` and
  `src/bijux_pollenomics/data_downloader/sources/` for source-specific
  collection structure
- `src/bijux_pollenomics/reporting/bundles/` and
  `src/bijux_pollenomics/reporting/map_document/` for publication assembly
- `src/bijux_pollenomics/reporting/context/` for the map-layer integration
  surface that joins normalized records to visible atlas output

## Read Across The Package

- open [Foundation](../foundation/index.md) when the structural question is
  really an ownership question
- open [Interfaces](../interfaces/index.md) when architecture reaches a public
  command, config, or artifact contract
- open [Operations](../operations/index.md) when structure affects repeatable
  rebuild or release workflows
- open [Quality](../quality/index.md) when you need proof that the documented
  structure is still protected

## Reader Takeaway

Use `Architecture` to make the runtime flow legible enough that a reviewer can
say where commands are parsed, where tracked data is rewritten, and where
publication output is assembled. If that answer only works from private memory,
the structure is still too implicit to maintain safely.
