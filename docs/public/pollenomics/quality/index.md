---
title: Verification and Limits
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Checks And Current Limits

This section answers the most important public question in the repository:
how much trust should a reader place in the current outputs, and where should
that trust stop.

That question matters because `bijux-pollenomics` publishes visible maps,
reports, and evidence summaries that can look more complete than the weakest
supporting material really is. A serious public quality section therefore has
to do two jobs at once:

- explain how the repository checks itself
- explain why some stronger claims are still refused

Use this section when the question is not "where is the code," but:

- what has actually been validated here
- which surfaces are strong enough for orientation, reuse, or citation
- what still remains partial, thin, blocked, or explicitly caveated
- how the repository avoids sounding more certain than its evidence deserves

## Start Here

- start with [runtime invariants and limits](runtime-invariants-and-limits.md)
  if you want the shortest explanation of what must stay true and what still
  remains weak
- use [test strategy](test-strategy.md) if you want to know how the repository
  chooses between unit, regression, and end-to-end checks
- use [change validation](change-validation.md) if you want to know what kind
  of proof a change owes before commit
- use [public language guide](public-language-guide.md) if you want to know why
  some phrases are allowed and others are rejected
- use [review checklist](review-checklist.md) if you want a short practical
  review pass for runtime, data, reporting, and docs changes
- use the linked report surfaces when you want the live repository posture
  rather than handbook explanation:
  [animal atlas readiness](../../../report/animal_atlas_readiness.md),
  [animal output honesty](../../../report/animal_output_honesty.md),
  [animal atlas exclusion report](../../../report/animal_atlas_exclusion_report.md),
  [animal output audit](../../../report/animal_output_audit.md),
  [repository truth posture](../../../report/repository_truth_posture.md), and
  [repository claim audit](../../../report/repository_claim_audit.md)

## What This Section Helps A Reader Decide

- whether a visible output is mainly exploratory, reviewable, or strong enough
  for a narrower claim
- whether a weak-looking result comes from poor evidence, honest caveating, or
  missing recovery work
- whether a wording choice reflects real proof or only presentation polish
- whether a change in the repository story came from data movement, testing, or
  a public-language correction

## What Quality Means Here

Quality in this repository does not mean "everything passes and looks tidy."
It means the public story stays proportionate to the real evidence.

That includes:

- tests that fail close to the defect
- file and report contracts that remain inspectable
- public wording that does not outrun evidence strength
- visible caveats when the repository is still incomplete

## What This Section Refuses To Do

- treat a green test suite as permission for inflated public claims
- treat a polished map or report as stronger than the supporting evidence chain
- hide weak animal aDNA recovery behind broader pollenomics context
- collapse very different trust questions into one vague notion of "quality"
