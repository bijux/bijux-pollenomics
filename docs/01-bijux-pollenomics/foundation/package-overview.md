---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-pollenomics` exists so this repository can regenerate its evidence
workspace from stable commands instead of from hand-edited `data/` and
`docs/report/` trees. The package owns the runtime behavior that collects source
material, normalizes it into tracked layouts, and publishes the country bundles
and atlas pages readers see on `bijux.io`.

The package is intentionally file-oriented. It does not exist to host a live
web service, hide outputs behind an API, or make scientific claims on its own.
It exists to turn known inputs into reviewable, reproducible outputs that can be
inspected directly in the repository.

```mermaid
flowchart LR
    commands["stable runtime commands"]
    collect["source collection and normalization"]
    data["tracked data contracts under data/"]
    publish["country bundles and atlas outputs"]
    review["reader and reviewer inspection"]
    limits["not a live service or interpretation layer"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class commands,page collect;
    class data,publish,review positive;
    class limits caution;
    commands --> collect --> data --> publish --> review
    limits --> collect
```

## What It Owns

- the CLI and command dispatch for `collect-data`, `report-country`,
  `report-multi-country-map`, and `publish-reports`
- source-specific collection and normalization for AADR, boundaries, LandClim,
  Neotoma, SEAD, and RAÄ inputs
- the tracked layout contracts written under `data/`
- report and atlas bundle assembly under `docs/report/`

## What It Does Not Own

- long-term repository maintenance policy, CI orchestration, and shared
  maintainer automation
- scientific interpretation beyond what the checked-in artifacts explicitly
  present
- hosted serving infrastructure outside the generated documentation site

## Open This Page When

- someone asks what the package is fundamentally for
- a change proposal sounds broader than deterministic collection and
  publication
- you need the shortest honest explanation before reading deeper pages

## Choose Another Page When

- you already know the package purpose and need a precise ownership answer
- the real question is structural, such as where a handler or renderer lives
- you are validating a concrete command, file contract, or test obligation

## Read Next

- open [Ownership Boundary](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/ownership-boundary/) when you need to separate
  runtime responsibilities from maintainer or docs responsibilities
- open [Module Map](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/module-map/) when you need the structural
  layout behind the package summary
- open [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/) when the
  published output surface is the real concern
- open [Test Strategy](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/test-strategy/) when the next question is
  how the package proves its behavior

## Concrete Anchors

- `packages/bijux-pollenomics/src/bijux_pollenomics/`
- `packages/bijux-pollenomics/tests/`
- `data/`
- `docs/report/`

