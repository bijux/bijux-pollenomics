---
title: Verification and Limits
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Checks And Current Limits

This section explains how the repository earns confidence and where it still
refuses stronger claims. It is the reader-facing answer to a simple question:
how much trust should I place in the current outputs, and what is still missing?

That question matters here because the repository publishes visible outputs that
can look more complete than the weakest supporting evidence really is. A public
quality section should therefore do two things at once: explain what is tested,
and explain what still blocks stronger language.

## Start Here

- start with [test strategy](test-strategy.md) if you want to know how the
  repository chooses between unit, regression, and end-to-end checks
- use [change validation](change-validation.md) if you want to know what kind
  of proof a change owes before commit
- use [review checklist](review-checklist.md) if you want a short practical
  review pass for runtime, data, reporting, and docs changes
- use [public language guide](public-language-guide.md) if you want to know why
  some words are allowed and others are rejected
- use [runtime invariants and limits](runtime-invariants-and-limits.md) if you
  want the shortest explanation of what must stay true and what still remains
  weak
- use the linked report surfaces when you want live repository posture rather
  than handbook explanation:
  [animal atlas readiness](../../../report/animal_atlas_readiness.md),
  [animal output honesty](../../../report/animal_output_honesty.md),
  [animal atlas exclusion report](../../../report/animal_atlas_exclusion_report.md),
  [animal output audit](../../../report/animal_output_audit.md),
  [repository truth posture](../../../report/repository_truth_posture.md), and
  [repository claim audit](../../../report/repository_claim_audit.md)
