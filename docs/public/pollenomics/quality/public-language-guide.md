---
title: Public Language Guide
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Public Language Guide

`bijux-pollenomics` should read like a calm scientific product, not like an
operator notebook and not like a status theater dashboard. This page defines
the vocabulary used in code-owned report surfaces and in the handbook pages
that explain them.

Public language matters here because wording can inflate a weak surface without
changing a single data file. The repository therefore treats naming and phrasing
as part of the evidence contract, not as a cosmetic afterthought.

## Information Roles

- `review`: reader-facing judgment about whether one bounded surface is trusted
- `validation`: pass or fail structural checks on a governed surface
- `audit`: systematic inspection across many files, claims, or source families
- `truth`: claim-calibration surface that keeps scope and weakness explicit
- `summary`: aggregate orientation surface for readers or downstream tooling
- `coverage`: how much of a bounded domain is currently represented
- `readiness`: whether a publication surface currently clears its own bar
- `honesty`: public caveat surface that keeps limits visible beside outputs
- `ledger`: accumulated exclusions, conflicts, or unresolved caveats
- `matrix`: repeated comparison question across several domains or surfaces
- `workflow`: governed human review sequence for curation or release
- `queue`: ordered recovery pressure for still-blocked work

## Avoid These Words

- `viewer`: it describes a tool posture, not an evidence responsibility
- `packets`: it describes delivery format, not the question a surface answers
- `scorecard`: it sounds managerial and hides what is actually being reviewed
- polished labels that do not say what the page settles

These banned patterns are not about style preference alone. They are blocked
because they often hide the real question a surface answers.

## Provenance Wording

- say `sample-owned`, `project-level`, `supplementary-table`, or another exact
  provenance class when it matters
- name uncertainty directly instead of smoothing it into confident prose
- prefer `supports`, `anchors`, `suggests`, `blocks`, and `remains unresolved`
  over inflated verbs such as `proves` unless the surface genuinely does

## Geographic Wording

- distinguish `Nordic`, `country-filtered`, `Europe-plus`, and `comparator`
  scopes explicitly
- do not call a comparator-heavy or region-limited output `general` or
  `region-agnostic`
- name the filter boundary whenever a map or summary is scope-specific

## Publication Wording

- call a surface `publishable` only when the governed checks for that surface
  actually pass
- keep the strongest readiness language behind the release gate
- when evidence is partial, say `partial`, `thin`, `blocked`, or `contextual`
  rather than hiding that status in softer wording
