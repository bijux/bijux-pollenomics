---
title: End-State Product Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-06-28
---

# End-State Product Model

`bijux-pollenomics` has one intended product shape. It is not meant to be a
Nordic site with a few accidental side branches, and it is not meant to be a
stack of country bundles pretending to be a global system. The durable goal is
one repository that collects evidence broadly once, then publishes narrower
views from that same governed state.

That model matters now because the repository has started to publish richer
specialized packets, such as the Sweden lake ranking surfaces. Those additions
should strengthen the same product model, not create a parallel mini-product
with its own rules and language.

This page explains the strategic answer:

- why the repository is organized around world, regional, and country surfaces
- how those surfaces relate to one another
- why future countries or regions should extend the same product model instead
  of creating a parallel one
- what kind of reuse is reasonable even before every geography has its own
  published map atlas surface

## Product Shape

- `world` is the broadest public surface and the parent publication scope
- `Europe-plus` is the European bridge between world coverage and Nordic
  specialization
- `Nordic` is the dense regional surface where the repository currently places
  its richest contextual overlays
- `country` bundles are narrower public descendants of the same evidence
  state
- specialized packets such as Sweden lake ranking remain attached to those
  same surfaces instead of becoming a disconnected publication family

## Why This Shape Matters

If the repository treats world, region, and country publication as separate
products, every expansion becomes fragile. New countries then require renderer
forks, scope-specific documentation, and parallel truth rules. The end-state
model refuses that drift.

## Runtime Consequence

The runtime must keep one repeatable loop:

1. collect tracked source-family data into `data/`
2. normalize source-family evidence into reviewable files
3. review recovery depth, chronology meaning, and publication caveats
4. publish world, regional, and country outputs from that same governed state

When the repository publishes a shortlist, ranking, or overlay, that output
still has to fit this loop. It should remain traceable to tracked inputs,
reviewable logic, and scoped public honesty surfaces.

The important point is that these outputs are not separate editorial products.
They are different public cuts through one repository-owned evidence model.

## How To Use The Product Shape

- start with `world` when the question is broad and comparative
- drop to `Europe-plus` when the Nordic slice needs a wider European frame
- use `Nordic` when regional density and contextual layering matter most
- use country bundles when the question is explicitly local

You should not have to guess whether these are separate products. They are
filtered views of one product.

## What This Means For Reuse

If your geography is not yet published as a first-class atlas surface, this
model still tells you how to read the repository:

- use the broadest existing surfaces to understand the current evidence balance
- use the data handbook and source-family pages to see which evidence families
  could already support your question
- treat a future country or region as an extension of one governed system, not
  as a special case that needs a new product story

That is the real value of the end-state model. It keeps expansion disciplined
enough that new publication surfaces can be added without rewriting what the
repository is.

## What This Means For Expansion

Adding `Germany` or another future country must be boring:

- the country joins the published roster
- the governing filters admit it through the same scope plan
- its country bundle is emitted into `docs/report/countries/<country-slug>/`
- the broader world and Europe-plus surfaces continue to derive automatically
- docs and tests remain about the same product model instead of branching

The same rule applies to future special packets. Adding another lake program,
fieldwork shortlist, or regional ranking should feel like a disciplined
extension of one evidence system, not like the birth of a second product.

That is why the country onboarding contract and playbook matter. They are not
extra ceremony. They are proof that growth is part of the product design rather
than a one-off workaround each time a new country appears.
