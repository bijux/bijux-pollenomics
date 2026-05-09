---
title: End-State Product Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# End-State Product Model

`bijux-pollenomics` now has one explicit product shape. It is not a Nordic map
that accidentally grew broader neighbors, and it is not a pile of country
bundles pretending to be a global system. The durable target is one repository
that collects evidence broadly once, then publishes narrower views honestly.

## Product Shape

- `world` is the governing public surface and the parent publication scope
- `Europe-plus` is the stable European bridge between world coverage and Nordic specialization
- `Nordic` is the dense regional specialization where contextual overlays become intentionally richer
- `country` bundles are narrower reader-facing descendants of the same governed evidence state

## Why This Shape Matters

If the repository treats world, region, and country publication as separate
products, every expansion becomes fragile. New countries require renderer
surgery, scope-specific docs forks, and parallel truth rules. The end-state
model refuses that drift.

## Runtime Consequence

The runtime must keep one repeatable loop:

1. collect tracked source-family data into `data/`
2. normalize source-family evidence into reviewable files
3. review recovery depth, chronology meaning, and publication caveats
4. publish world, regional, and country outputs from that same governed state

## Reader Consequence

- start with `world` when the question is broad
- drop to `Europe-plus` when the Nordic slice needs a wider European frame
- use `Nordic` when regional context density matters
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

That is why the country onboarding contract and playbook exist. They are not
extra ceremony; they are the proof that global extensibility is now part of the
product design.
