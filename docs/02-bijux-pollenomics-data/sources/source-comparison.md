---
title: Source Comparison
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Source Comparison

Each source family in this repository answers a different kind of question.
They can appear together in one map or report, but that does not make their
evidence claims interchangeable.

## Comparison Model

```mermaid
flowchart TB
    aadr["AADR"]
    boundaries["boundaries"]
    landclim["LandClim"]
    neotoma["Neotoma"]
    raa["RAÄ"]
    sead["SEAD"]
    atlas["shared atlas view"]

    aadr --> atlas
    boundaries --> atlas
    landclim --> atlas
    neotoma --> atlas
    raa --> atlas
    sead --> atlas
```

Layers can render together while still meaning very different things.

## Which Source Helps With Which Question

- AADR supports human ancient DNA context and release-based sample metadata questions
- Boundaries support country framing, region filtering, and map context questions
- LandClim supports pollen sequence and REVEALS context questions
- Neotoma supports paleoecological pollen-site context questions
- RAÄ supports Sweden-scoped archaeology context questions
- SEAD supports broader environmental archaeology context questions
- animal source intake supports project recovery, supplement capture, and non-human sample extraction questions

## Good Reader Rule

- open [Source family matrix](source-family-matrix.md) when the question is repository balance
- open [Animal source intake](animal-source-intake.md) when the question is paper, supplement, or sample recovery

## Why This Comparison Matters

The common failure is to compare sources by how they look on a map instead of
by the narrower question each one can honestly answer.
