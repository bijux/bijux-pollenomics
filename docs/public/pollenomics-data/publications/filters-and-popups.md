---
title: Filters and Popups
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Filters and Popups

Filters and popups are the reader's first explanation layer on the map. They
should help a person understand what they are seeing without making the atlas
look simpler or stronger than it really is.

That matters because the map changes by scope. World, Europe-plus, Nordic, and
country views do not all show the same layers, and a popup is not allowed to
quietly inflate a thin record into a confident story.

## What Readers Should Be Able To Learn Immediately

- which countries are active in one scope
- which point layers remain visible after geography filtering
- why Nordic-only context overlays disappear when a reader moves back to world
  or Europe-plus
- whether animal points belong to the world surface only or to narrower derived
  views
- whether a country bundle is derived from the world surface directly or
  through a regional parent

The point of the inspection surface is not decoration. It is to keep geography
selection auditable for readers who did not write the code.

## What Filters Are For

- filters show which geography and layer choices are active
- filters keep scope changes visible instead of making them feel like a hidden
  frontend preference
- filters stop a world, regional, and country map from pretending to be the
  same view with different zoom levels

## What Popups Are For

- tell the reader what kind of point or layer they are looking at
- expose the compact facts needed for orientation without replacing the deeper
  evidence page
- send the reader toward the next narrower audit when the visible summary is
  not enough

## What These Surfaces Must Not Do

- hide why a point appears in one scope and not another
- make contextual layers read like sample-backed proof
- make a broad-area or weakly located record sound precise
- let frontend convenience outrun publication rules

## When To Leave The Popup

Leave the popup and move to a narrower page when:

- a visible point looks more precise than expected
- one layer disappears between scopes and the change matters
- the reader needs chronology, locality, or provenance rather than a compact
  label
- the public wording sounds stronger than the evidence probably allows

## Follow-Up Pages

- use [maps](maps.md) for the wider scope picture
- use [point rules](point-rules.md) for why a point can publish at all
- use [map inputs](map-inputs.md) for the files behind the visible result
- use [limits](limits.md) when the honest answer may be blockage or weakness

## Nordic Atlas Filters And Popups

The Nordic atlas inherits these filtering rules from the wider publication
geography contract. Its popups should explain visibility and caveat posture,
not hide selection logic behind front-end convenience.
