---
title: SEAD Handbook
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# SEAD Handbook

This handbook explains how `bijux-pollenomics` treats SEAD as a contextual
archaeology source family.

## What SEAD Is Here

SEAD is a site-level archaeology context layer. It can help readers see
broader environmental or settlement context around pollen and animal evidence,
but it should not be read like one uniform chronology source.

The repository can currently mirror three things with confidence:

- raw site inventory capture under `data/sead/raw/`
- normalized contextual point layers under `data/sead/normalized/`
- explicit review packets under `data/sead/review/`

The repository does not mirror the full upstream SEAD browsing experience or
the whole relational database. When the checked-in row is thin, the stable
reader path is still the upstream SEAD site page.

## Access Model

The governed access model lives in `data/sead/review/access_model.json`.

It distinguishes:

- what the repository mirrors directly
- what it only references through stable upstream links
- what still requires reader inspection at the source
- what the repository should not pretend to redistribute

This matters because a contextual source can be easy to misread when the local
artifact looks complete but the real interpretive detail still lives upstream.

## Time and Period Semantics

The governed time review lives in `data/sead/review/temporal_review.json`.

SEAD rows may appear as:

- numeric site spans
- numeric spans with contextual caveats
- period labels without stable numeric support
- thin inventory rows that remain unresolved

Those states are not interchangeable. They are the difference between a row
that can support bounded time filtering and a row that should remain a broad
context cue.

## Legibility and Risk

The main per-row review surface is
`data/sead/review/evidence_legibility_review.json`.

It classifies rows by:

- temporal strength
- duration posture
- access visibility
- normalization risk

That packet is the best short answer when a maintainer or reviewer asks
whether SEAD is merely present or actually inspectable.

## Publication Boundary

SEAD is published as archaeology context. It does not become a direct evidence
surface simply because it is visible in report bundles.

The report-root summary for this posture is
[`docs/report/repository_sead_legibility_review.md`](../../../report/repository_sead_legibility_review.md).

## Recovery Roadmap

The recovery roadmap lives in `data/sead/review/recovery_roadmap.json`.

It names the concrete deliverables still needed to move SEAD from thin site
inventory plus derived maps toward a source family that is both scientifically
legible and operationally trustworthy.
