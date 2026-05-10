---
title: Runtime Purpose and Boundary
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# What This Repository Is For

This repository exists to make one evidence publication loop visible and
repeatable. It takes several evidence families that would otherwise stay
scattered across papers, tables, maps, and local scripts, and turns them into
one reviewable repository state.

In practical terms, `bijux-pollenomics` owns the path from tracked source
material to tracked public output. That includes collection, normalization,
publication, and the checks that stop the repository from sounding more certain
than the evidence really is.

This page answers the first practical question the public guide should resolve:
what is this repository actually for, and why does it need one owned runtime at
all?

## The Short Answer

The repository is trying to do one specific thing well: publish inspectable
cross-evidence outputs without hiding where they came from. It is not here just
to display a map, and it is not yet a finished scientific engine that settles
every pollen, archaeology, and ancient-DNA question.

Its value comes from joining three responsibilities that often drift apart:

- collecting and refreshing governed source material
- normalizing that material into repository-owned evidence files
- publishing downstream outputs that people can inspect and question

If those responsibilities split into private scripts, ad hoc notebooks, and a
separate presentation layer, the public outputs may still look polished, but
they stop being accountable.

## What The Runtime Must Keep Legible

- command entrypoints that rewrite tracked state
- source-family and normalized evidence files under `data/`
- country, regional, and world publication outputs under `docs/report/`
- tests and reviews that fail when those publication contracts drift

## Start With These Questions

- [repository scope and limits](repository-scope-and-limits.md): what the
  repository claims today and where it stops
- [end-state product model](end-state-product-model.md): how world, region, and
  country outputs fit together as one product rather than several unrelated
  websites
- [pollenomics engine roadmap](pollenomics-engine-roadmap.md): what broader
  pollenomics ambition still remains ahead of the current state
- [runtime scope and ownership](runtime-scope-and-ownership.md): what this
  runtime owns inside the repository and what it deliberately leaves elsewhere

## Why This Matters

A public guide should not make people reconstruct the product from code names.
It should answer three basic questions quickly:

- what kinds of evidence are included here
- what happens to those inputs before they become public outputs
- how much confidence the repository claims, and where it refuses stronger
  language

That is the boundary this section protects. It explains the product first, then
the code ownership that makes the product rebuildable.

## Ownership Boundary

- the runtime owns collection, normalization, and publication behavior
- the data handbook owns source provenance and tracked file meaning
- the atlas handbook owns how visible map surfaces should be interpreted
- the maintainer handbook owns release, documentation shell, and
  repository-health rules

## Where To Go Next

- stay in this section if your question is "what is this repository trying to
  do, and how honest is it about its current state?"
- move to [end-state product model](end-state-product-model.md) if your
  question is how world, Europe-plus, Nordic, and country outputs fit together
- move to [the data guide](../../pollenomics-data/index.md) if your question is
  which source family, paper, site, sample, or chronology record supports a
  visible claim
- move to [the Nordic atlas guide](../../nordic-atlas/index.md) if your
  question is how a visible map point should be read, filtered, or challenged
