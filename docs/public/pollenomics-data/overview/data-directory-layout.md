---
title: Data Directory Layout
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Data Directory Layout

This page explains the shape of the main repository-owned data tree for readers
who need a file-system map after they already understand the product model.

## How To Read The Tree

The directory layout makes most sense when you read it by role, not by
alphabetical path order:

- `data/` holds source capture, normalization, and review material
- `docs/report/` holds generated public bundles and review packets
- `docs/public/pollenomics-data/` explains what those tracked files mean

## Main Areas

| Area | What lives there | Why it matters |
| --- | --- | --- |
| `data/aadr/` | human ancient DNA release material | release-based human context |
| `data/adna/` | animal aDNA governance, normalized species data, and final atlas inputs | sample-backed animal evidence chain |
| `data/landclim/` | pollen sequence and REVEALS context | environmental background |
| `data/neotoma/` | paleoecological pollen context | environmental comparison and extension |
| `data/sead/` | environmental archaeology context | archaeology and environmental support |
| `data/raa/` | Swedish archaeology context | Sweden-specific archaeology framing |
| `data/boundaries/` | country and region framing geometry | filtering and scope clarity |
| `docs/report/` | generated world, regional, and country publication bundles | public-facing outputs |

## Reader Rule

If your question is about meaning, start with the handbook pages first. If your
question is about exact file locations, use this page after that. The tree is
much easier to understand once the roles of source, evidence, review, and
publication are already clear.
