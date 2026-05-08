---
title: Repository Governance
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-08
---

# Repository Governance

`bijux-pollenomics-dev` is the maintainer package that turns repository-health
rules into executable checks. It is not a second runtime and it is not the
owner of source collection.

## Package Boundary

- `docs/` checks documentation integrity and public-surface breadth
- `release/` checks claim posture and repository-truth gates
- `quality/` holds maintainer-only validators and review helpers
- `api/` supports frozen API contract review

## Module Map

Read `bijux-pollenomics-dev` as three owned enforcement groups:

- docs integrity
- release and claim governance
- maintainer-only quality or contract helpers

## Governance Scope

This package owns:

- docs breadth and docs-link integrity checks
- release-support rules for report posture and claim language
- schema or API governance that belongs to repository publication integrity

This package does not own:

- source-family collection logic
- sample extraction logic
- atlas rendering logic

## Schema And Scope Governance

- schema or frozen-contract changes belong here when they affect public review
- source semantics and scientific interpretation do not
- the package should stay narrow enough that runtime ownership remains obvious

## Security And Release Pressure

Maintainer code must fail when:

- public docs become narrower than the repository evidence story
- release surfaces imply stronger readiness than tracked evidence supports
- frozen contract files drift without deliberate regeneration
- security or policy gates are bypassed by convenience command routing
