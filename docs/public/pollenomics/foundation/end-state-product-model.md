---
title: End-State Product Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# End-State Product Model

`bijux-pollenomics` has one intended product shape. It is not supposed to be a
Nordic site with a few accidental side branches, and it is not supposed to be a
stack of country bundles pretending to be a global system. The durable goal is
one repository that collects evidence broadly once, then publishes narrower
views from that same governed state.

## Product Shape

- `world` is the broadest public surface and the parent publication scope
- `Europe-plus` is the European bridge between world coverage and Nordic
  specialization
- `Nordic` is the dense regional surface where the repository currently places
  its richest contextual overlays
- `country` bundles are narrower reader-facing descendants of the same evidence
  state

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

The important point is that these outputs are not separate editorial products.
They are different public cuts through one repository-owned evidence model.

## Reader Consequence

- start with `world` when the question is broad and comparative
- drop to `Europe-plus` when the Nordic slice needs a wider European frame
- use `Nordic` when regional density and contextual layering matter most
- use country bundles when the question is explicitly local

The reader should never have to guess whether these are separate products. They
are filtered views of one product.

## Expansion Consequence

Adding `Germany` or another future country must be boring:

- the country joins the published roster
- the governing filters admit it through the same scope plan
- its country bundle is emitted into `docs/report/countries/<country-slug>/`
- the broader world and Europe-plus surfaces continue to derive automatically
- docs and tests remain about the same product model instead of branching

That is why the country onboarding contract and playbook matter. They are not
extra ceremony. They are proof that growth is part of the product design rather
than a one-off workaround each time a new country appears.
