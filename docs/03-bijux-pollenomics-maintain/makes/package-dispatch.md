---
title: Package Dispatch
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Package Dispatch

Package dispatch is driven by `makes/packages.mk` and shared catalog helpers.

## Dispatch Model

```mermaid
flowchart TB
    catalog["package catalog helpers"]
    dispatch["makes/packages.mk dispatch"]
    primary["bijux-pollenomics"]
    compat["pollenomics"]
    maintain["bijux-pollenomics-dev"]

    catalog --> dispatch
    dispatch --> primary
    dispatch --> compat
    dispatch --> maintain
```

This page should make package dispatch feel like explicit routing, not
incidental iteration. The repository needs readers to see which package role
each target lands on before they assume one command path fits every package.

## Current Package Records

- `bijux-pollenomics` as the primary package with check, build, SBOM, and API
  surfaces
- `pollenomics` as the compatibility package
- `bijux-pollenomics-dev` as the maintainer package

## Design Pressure

The common failure is to flatten packages into one shared command surface,
which hides why compatibility and maintainer packages need different dispatch
behavior than the primary product package.
