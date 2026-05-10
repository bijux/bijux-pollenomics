---
title: Runtime Invariants and Limits
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Runtime Invariants and Limits

This page states the public ground rules of the repository: what must stay true
even while weaker evidence families are still being recovered, and what should
not be inferred from the current outputs.

It is deliberately short because these are the rules that should remain clear
even when the rest of the handbook becomes more detailed.

## Invariants

- commands rewrite governed roots rather than ad hoc destinations
- source-family ownership stays visible in tracked data layout
- publication outputs remain downstream of tracked repository state
- docs and review surfaces must not hide weak evidence posture

These invariants are not implementation preference. They are the conditions
that keep the public product reviewable.

## What These Invariants Mean In Practice

- a visible output should always trace back to a stable repository-owned path
- one source family should not disappear into a generic mixed bucket
- maps and reports should remain the downstream explanation, not the upstream
  proof
- caveats and refusal language should survive even when the interface becomes
  cleaner

## Definition Of Done

A change is not done when files merely exist. It is done when the changed
boundary is reviewable, linked, and validated at the right layer.

For the public product, that means:

- the changed surface can be inspected
- the next narrower explanation still exists
- the wording still matches the available proof
- the repository has not silently traded clarity for elegance

## Dependency Governance

Prefer explicit runtime contracts and stable checked-in files over hidden
side effects or opaque rebuild steps.

That matters because people should not need maintainer folklore to understand
how a claim became visible.

## Known Limits

- animal aDNA remains a partial recovery surface
- atlas presence is not the same as scientific completeness
- docs breadth can regress if it is not tested explicitly

## What The Current Outputs Still Cannot Honestly Claim

- that the animal aDNA side is already a finished, evenly recovered evidence
  engine
- that all visible points carry the same locality and chronology strength
- that broader geography automatically means deeper proof
- that a cleaner handbook means the repository itself has become more complete

## Risk Posture

The main risk is elegant-looking narrowing: fewer pages, fewer links, and
fewer explicit caveats while the repository still claims to explain the same
evidence landscape.

That is why the repository treats clarity as part of technical quality. A
surface that sounds cleaner but says less is often a regression, not an
improvement.
