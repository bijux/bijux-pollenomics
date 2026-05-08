---
title: Change Validation
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Change Validation

Every runtime change should prove the boundary it touched.

## Validation Layers

- unit tests for narrow logic and file-shape contracts
- regression tests for repository-owned docs, outputs, and public file presence
- command-level rebuilds when a change affects tracked `data/` or `docs/report/`
- repository-truth packets when a change affects breadth, posture, or public
  claim language

## Minimum Rule

If a change rewrites tracked outputs, validate both the generator and the
generated destination before committing.

## Breadth Rule

Docs work is not exempt. A docs rewrite fails review if it narrows `01`,
`02`, or `03` without an equally informative replacement that is present and
linked.
