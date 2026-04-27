---
title: CI Targets
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# CI Targets

CI reuses the same repository and package targets exposed through Make.

## CI Target Model

```mermaid
flowchart TB
    make["make target surface"]
    repo["repository checks"]
    package["package checks"]
    workflows["GitHub workflows"]
    verdict["CI verdict"]

    make --> repo
    make --> package
    repo --> workflows
    package --> workflows
    workflows --> verdict
```

This page should show CI as reuse rather than reinvention. The important point
is that GitHub workflows are not inventing a second verification system; they
are driving the same target surface readers can run locally.

## Common Targets

- `check`
- `lint`
- `test`
- `quality`
- `security`
- `docs`
- `api`
- `build`
- `sbom`

## Design Pressure

The common failure is to treat CI target names as labels only, which hides how
they map back to repository and package checks that should stay coherent across
local and GitHub execution paths.
