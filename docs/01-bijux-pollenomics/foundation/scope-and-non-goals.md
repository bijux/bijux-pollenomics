---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Scope and Non-Goals

`bijux-pollenomics` is scoped to deterministic collection and publication work.
Its most attractive wrong expansion is to turn visible map or source material
into a broader interpretation or ranking system inside the runtime package.

## In Scope

- downloading or refreshing supported source datasets
- normalizing those sources into stable, reviewable files
- publishing country report bundles and the Nordic Evidence Atlas
- exposing configuration defaults that keep those workflows explicit

## Out Of Scope

- genotype processing beyond public AADR metadata files
- lake-intersection analysis, ranking logic, or site recommendation
- automated field recommendation or site-selection decisions
- mutable hosted application behavior that depends on server state

## First Proof Check

- `src/bijux_pollenomics/data_downloader/`
- `src/bijux_pollenomics/reporting/`
- `docs/02-bijux-pollenomics-data/`
- `docs/05-nordic-evidence-atlas/`

## Boundary Test

If a change increases scientific ambition or product breadth without preserving
deterministic file outputs and clear review boundaries, it does not belong in
this package yet.
