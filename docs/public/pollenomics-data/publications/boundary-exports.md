---
title: Boundary Exports
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Boundary Exports

Boundary exports are the public framing surfaces for country and region
boundaries. Their job is to make geographic filtering, scope limits, and map
interpretation legible.

They matter because the public product would become misleading very quickly
without a disciplined geography layer. You need to know what "Nordic,"
"country," or "world" actually means on the map, and you need to know that
those scopes are applied consistently rather than by visual guesswork.

## What Boundary Exports Make Clear

- what geography a public map or report scope is actually using
- why one visible point appears in one scope but not another
- how country, regional, and world views stay aligned instead of drifting into
  ad hoc filtering
- whether a disagreement is really about evidence or only about map framing

## What Boundary Exports Add To The Public Product

Boundary exports add:

- explicit country and region framing
- stable geography filters across report and atlas surfaces
- a common scope language for public users, auditors, and maintainers

## What They Do Not Do

Boundaries are not evidence of past activity. They should not be read as if
they:

- prove settlement, animal movement, or archaeological intensity
- make a visible geography scientifically stronger by themselves
- resolve sample-level locality or chronology questions

They are publication infrastructure. Their job is to make geography legible and
honest, not to add historical proof.

## Why This Page Matters Publicly

Without explicit framing, you could not tell whether an absent point
reflects weak evidence, a scope rule, or a rendering mistake. That is why this
page belongs on the public surface.

## If You Need The Repository-Owned Records

The normalized family outputs live under:

- `data/boundaries/normalized/`

If your question is about visible map behavior, continue to [maps](maps.md),
[filters and popups](filters-and-popups.md), or [limits](limits.md). If your
question is about the framing family itself, continue to
[boundary source guidance](../sources/boundaries.md).
