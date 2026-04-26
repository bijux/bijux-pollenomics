---
title: Migration Issues
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Migration Issues

The data handbook migration is meant to reduce ambiguity, but it carries real
risks if handled casually.

## Current Migration Issues

- old flat docs and the new data reference can disagree if both are edited in
  parallel
- cross-links can break when pages move from generic directories into
  `docs/02-bijux-pollenomics-data/`
- reviewers may miss data-contract changes if nav and file moves are separated

## Mitigation

- move navigation and content together in the final migration step
- keep source and output names stable while the docs shape changes
- verify the site strictly after each batch

