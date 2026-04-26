---
title: Normalized AADR Outputs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Normalized AADR Outputs

AADR outputs remain versioned under `data/aadr/<version>/`.

## What This Output Family Carries

- sample metadata and locality records used by country bundles and the atlas
- visible version identity in the tracked tree
- the strongest direct line from AADR refreshes to public publication changes

## Boundary

These files are repository-owned normalized outputs, not the entire upstream
release and not genotype analysis artifacts. Their role is to make the checked-in
sample layer reviewable and publishable.

## First Proof Check

- inspect `data/aadr/v66/`
- compare with [AADR](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/aadr/)
  when the question is about upstream scope rather than checked-in outputs
