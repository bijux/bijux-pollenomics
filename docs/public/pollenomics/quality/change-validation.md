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

This page exists because not every change needs the same proof. A wording fix,
a source-normalization rule, and a publication-output change do not carry the
same risk. Good validation matches the boundary that changed.

For a reader, the deeper point is simple: a serious repository should be able
to say why it trusts one change and what kind of proof that trust is based on.

## Validation Layers

- unit tests for narrow logic and file-shape contracts
- regression tests for repository-owned docs, outputs, and public file presence
- command-level rebuilds when a change affects tracked `data/` or `docs/report/`
- repository truth reviews when a change affects breadth, posture, or public
  claim language

## Match Proof To Risk

- a local helper change should not need the same proof as a public output
  rewrite
- a docs wording change is not "just docs" if it changes what readers are led
  to believe
- a generated report change is incomplete if only the source code was checked
  and the generated destination was ignored

## Minimum Rule

If a change rewrites tracked outputs, validate both the generator and the
generated destination before committing.

That rule matters because a repository like this publishes both code and
checked-in public surfaces. One without the other is not enough proof.

## Breadth Rule

Docs work is not exempt. A docs rewrite fails review if it narrows `01`,
`02`, or `03` without an equally informative replacement that is present and
linked.

The larger point is that passing tests are not enough when a rewrite makes the
public explanation thinner or more confusing. Public clarity is also part of
the contract.

## Reader Consequence

When the repository changes what it says in public, the validation burden is
not only technical. The maintainers also owe proof that the new explanation is
still broad enough, linked enough, and honest enough for a reader to rely on.
