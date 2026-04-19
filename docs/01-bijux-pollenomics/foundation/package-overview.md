---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Package Overview

`bijux-pollenomics` exists so the repository can rebuild a checked-in evidence
workspace from stable commands instead of hand-edited data and report trees.
Its job is to own the runtime behavior for collecting source data, normalizing
it into tracked layouts, and publishing the atlas and country bundles that the
docs site exposes.

The package is intentionally file-oriented. It does not exist to host a live
web service or to make research claims on its own. It exists to turn known
inputs into reviewable, reproducible outputs.

## What It Owns

- the CLI and command dispatch for `collect-data`, `report-country`,
  `report-multi-country-map`, and `publish-reports`
- source-specific collectors for AADR, boundaries, LandClim, Neotoma, SEAD,
  and RAÄ
- normalized data layout rules under `data/`
- report bundle assembly under `docs/report/`

## What It Does Not Own

- long-term repository maintenance policy and CI orchestration
- scientific interpretation beyond what the checked-in artifacts can show
- hosted serving infrastructure outside the generated docs site

## Concrete Anchors

- `packages/bijux-pollenomics/src/bijux_pollenomics/`
- `packages/bijux-pollenomics/tests/`
- `data/`
- `docs/report/`

## Purpose

This page gives the shortest honest description of why the runtime package
exists.

## Stability

Keep it aligned with the package code, tracked outputs, and public command
surface that actually ship in this repository.
