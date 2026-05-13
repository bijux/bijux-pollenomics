---
title: Sources
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Sources

This section explains where the repository's evidence comes from before that
evidence is turned into maps, tables, and public summaries.

That matters because `bijux-pollenomics` is not built from one source family.
It combines pollenomics records, archaeology context, geographic framing
layers, human ancient DNA releases, and a separate animal ancient DNA intake
program. Those materials can appear together in one public product, but they
do not answer the same question and they should not be trusted for the same
reason.

## Why This Section Exists

Readers usually want a simple answer to one of these first questions:

- what kind of evidence is this repository actually built from?
- which source family should I trust for the question I care about?
- why can some layers travel across many regions while others are local or
  still incomplete?
- what is the difference between a published map layer and the underlying
  source work that made it possible?

The pages in this section are here to answer those questions directly, in
public language, before you have to think about repository layout.

## The Main Source Families

| Family | What it mainly contributes | Best first use |
| --- | --- | --- |
| [LandClim](landclim.md) | pollen sequence and REVEALS context | environmental setting and broad vegetation interpretation |
| [Neotoma](neotoma.md) | paleoecological pollen-site context | site-centered pollen comparison across geography |
| [SEAD](sead.md) | environmental archaeology context | wider archaeological context beyond one national system |
| [RAÄ](raa.md) | Sweden-specific archaeology context | dense Swedish and Nordic archaeological reading |
| [Boundaries](boundaries.md) | country and region framing | filtering and geographic scope interpretation |
| [AADR](aadr.md) | human ancient DNA release context | human aDNA comparison beside pollen and archaeology |
| [Animal source intake](animal-source-intake.md) | project, paper, supplement, and sample recovery for non-human aDNA | understanding what had to be recovered before animal aDNA can be published |

## How To Use These Pages

Start with [Source comparison](source-comparison.md) if you want the quickest
answer to "which source family can answer my question?"

Open [Source family matrix](source-family-matrix.md) if you want to compare the
whole repository at once: evidence type, geographic reach, publication role,
and main limits.

Then move into the family pages only after you know what kind of source you are
reading about. The short family pages explain the public meaning of each
source. The longer process pages explain the harder cross-cutting ideas such as
[Refresh policy](refresh-policy.md), [Shared normalization](shared-normalization.md),
and the animal recovery chain.

## What Readers Should Take Away

- A mixed map is not a single kind of evidence.
- Pollenomics remains core to the repository, not decorative context around an
  ancient DNA story.
- Archaeology and boundaries help interpretation, but they do not make direct
  biological claims on their own.
- Human aDNA and animal aDNA are separate source programs with different
  maturity and different review burdens.
- Public outputs are downstream products. They are not the same thing as the
  source material that supports them.

## If You Need The Underlying Repository-Owned Records

Most readers will not need to open tracked files directly. If you do, the
high-signal cross-family records are:

- `data/collection_summary.json`
- `data/adna/governance/source_library/project_source_evidence_matrix.json`
- `data/adna/governance/source_library/project_registry.json`
- `data/adna/governance/source_library/paper_registry.json`
- `data/adna/governance/source_library/source_intake_audit.json`
- [source family matrix](source-family-matrix.md)

Those records are useful after you understand the source families, not before.
