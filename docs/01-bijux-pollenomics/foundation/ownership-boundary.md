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
and tracked publication artifacts. It is where reviewers look for
output-shaping logic.

The package does not own generic repository health automation. That work lives
with `bijux-pollenomics-dev`, the make system, and GitHub workflows so runtime
changes and maintenance changes can be reviewed separately.

```mermaid
flowchart LR
    runtime["runtime package"]
    collect["collection and normalization rules"]
    publish["report and atlas output shaping"]
    maintain["maintainer tooling and CI"]
    docs["explanatory docs and route pages"]
    decision["reader question<br/>where should this change live?"]
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

- `command_line/` for public command registration, parsing, and dispatch
- `data_downloader/` for source collection, staging, layout rules, and
  normalization
- `reporting/` for country bundles, atlas generation, map payloads, and
  artifact rendering
- `config.py` for package defaults and path contracts

## Adjacent Areas

- `packages/bijux-pollenomics-dev/` for repository-quality tooling
- `makes/` for command orchestration and shared automation contracts
- `docs/` for the checked-in explanatory surface that points at runtime outputs

## Open This Page When

- a pull request crosses from package code into repository automation
- the same change seems to belong partly in runtime and partly in docs or CI
- reviewers need a crisp answer about ownership before debating implementation

## Decision Rules

- keep a change in `bijux-pollenomics` when it changes command behavior,
  source handling, tracked data layout, or published artifact content
- move a change to maintainer surfaces when it changes how the repository
  validates, formats, or orchestrates work across packages
- update docs alongside runtime code when public behavior changes, but do not
  relocate output-shaping logic into Markdown just because it is easier to edit

## Common Boundary Mistakes

- treating generated report paths as a docs-only concern instead of a runtime
  contract
- moving validation expectations into runtime docs when the real owner is the
  maintainer package or workflow layer
- burying package defaults in ad hoc scripts instead of in the tracked config
  and command surfaces

## Read Next

- open [Package Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/package-overview/) when the disagreement is still
  about the runtime’s basic purpose
- open [Module Map](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/module-map/) when ownership depends on
  where a behavior sits in the codebase
- open [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/) when the
  argument is really about checked-in output surfaces
- open [Test Strategy](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/test-strategy/) when the next question is
  which proof surface should move with the change

## Bottom Line

The runtime owns the code that shapes evidence outputs. Maintainer layers own
how the repository drives, validates, and governs that code. Keeping those
boundaries honest keeps review scope honest too.

