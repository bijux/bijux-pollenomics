---
title: Normalized SEAD Outputs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Normalized SEAD Outputs

SEAD normalized outputs live under `data/sead/normalized/`.

## SEAD Output Model

```mermaid
flowchart TB
    upstream["SEAD archaeology source"]
    normalized["normalized SEAD outputs"]
    atlas["atlas archaeology context layers"]
    reader["broader archaeology context question"]

    upstream --> normalized
    normalized --> atlas
    atlas --> reader
```

This page should show why SEAD belongs beside RAÄ without becoming identical to
it. SEAD gives broader archaeology context, but it still carries its own source
story and interpretation limits.

## What This Output Family Carries

- environmental archaeology site records in CSV and GeoJSON form
- a broader archaeology context family than the Sweden-only RAÄ surface
- atlas-ready files that keep source ownership visible

## Boundary

These files add contextual archaeology layers to the atlas. They do not become
equivalent to RAÄ just because both are archaeology context, and they do not
replace source-specific interpretation.

## First Proof Check

- inspect `data/sead/normalized/`
- compare with [SEAD](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/sead/)
  when the question is about the upstream family rather than the output shape

## Design Pressure

The easy failure is to flatten archaeology context into one interchangeable
layer family, which makes broader SEAD context and Sweden-scoped RAÄ context
look more comparable than they really are.
