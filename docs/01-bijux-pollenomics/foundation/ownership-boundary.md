---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

The runtime package owns the behavior that turns source inputs into tracked data
and tracked publication artifacts. It should be the place where reviewers look
for output-shaping logic.

The package does not own generic repository health automation. That work lives
with `bijux-pollenomics-dev`, the make system, and GitHub workflows so runtime
changes and maintenance changes can be reviewed separately.

```mermaid
flowchart LR
    runtime["runtime package"]
    collect["collection and normalization logic"]
    publish["report and atlas publishing"]
    maintain["maintainer tooling and CI"]
    docs["docs explanation surface"]
    decision["where should this change live?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class runtime,page decision;
    class collect,publish positive;
    class maintain,docs caution;
    runtime --> collect
    runtime --> publish
    maintain --> decision
    docs --> decision
    runtime --> decision
```

## Package-Owned Areas

- `command_line/` for public command registration and dispatch
- `data_downloader/` for source collection, staging, and normalization
- `reporting/` for country bundles, atlas generation, and artifact rendering
- `config.py` for package defaults and path contracts

## Adjacent Areas

- `packages/bijux-pollenomics-dev/` for repository-quality tooling
- `makes/` for command orchestration and shared automation contracts
- `docs/` for the checked-in explanatory surface that points at runtime outputs

## Use This Page When

- a pull request crosses from package code into repository automation
- the same change seems to belong partly in runtime and partly in docs or CI
- reviewers need a crisp answer about ownership before debating implementation

## Purpose

This page helps reviewers decide whether a change belongs in the runtime
package or in an adjacent maintenance surface.
