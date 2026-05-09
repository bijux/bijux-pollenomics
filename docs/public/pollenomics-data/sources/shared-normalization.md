---
title: Shared Normalization
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Shared Normalization

Different source families enter the repository in very different shapes, but
they still need a shared normalization discipline so they can appear together
without turning into one shapeless export.

## What Shared Normalization Means

Shared normalization does not force every source to have identical fields. It
means the repository gives each family a predictable stage where the material
is converted into repository-owned evidence artifacts with known roles.

That shared discipline is what makes it possible to compare:

- source capture versus public publication
- one domain against another
- visible points against the narrower evidence files that support them

## Where To Inspect It

- normalized source-family outputs live in family-owned paths such as
  `data/landclim/normalized/`, `data/neotoma/normalized/`, and
  `data/sead/normalized/`
- the public publication side starts under `docs/report/world/` and then narrows
  into regional and country bundles

Normalization is what lets those very different families meet without becoming
one shapeless export.

## Why Readers Benefit

Readers usually notice normalization only when it is missing. Without it, a
mixed repository becomes a mixture of raw tables, ad hoc exports, and public
pages that cannot be compared honestly.
