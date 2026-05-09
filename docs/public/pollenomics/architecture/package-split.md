---
title: Package Split
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Package Split

`bijux-pollenomics` ships three distributions because they serve three
different audiences. The split is acceptable only because the ownership line
is sharp.

## Canonical Runtime

`packages/bijux-pollenomics/` owns the runtime command surface, source-family
collection, animal aDNA evidence recovery, evidence review, and publication
assembly.

If a change affects:

- tracked files under `data/`
- publication artifacts under `docs/report/`
- the scientific meaning of intake, normalization, review, or reporting

then the change belongs in `bijux_pollenomics`.

## Maintainer Toolkit

`packages/bijux-pollenomics-dev/` owns maintainer checks, docs integrity,
release support, and repository-health tooling.

It does not own:

- project admission rules
- source collection logic
- sample, site, chronology, or coordinate normalization
- atlas or country publication behavior

That package should test or validate the runtime. It should not quietly become
another runtime.

## Alias Distribution

`packages/pollenomics/` is a compatibility alias. It exists for the shorter
package name and CLI command, not for independent scientific behavior.

The alias may:

- re-export the public Python API
- delegate CLI parsing and dispatch to the canonical runtime

The alias may not:

- invent new collection logic
- publish different report behavior
- drift into a second conceptual product

## Why This Matters

This repository is already structurally dense. A clean package split prevents
future work from hiding scientific logic in maintainer tooling or from letting
the alias package drift away from the canonical runtime.
