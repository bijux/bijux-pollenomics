---
title: Sample Records
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Sample Records

The sample record is the durable unit of the animal ancient DNA database.
Projects, papers, supplements, locality decisions, chronology review, and map
outputs all meet here.

If a reader wants to know what the repository actually knows about one animal
record, this is the first place to start. Everything else downstream depends on
the sample being stable enough to carry forward.

## What A Sample Record Should Answer

A serious sample record should answer these questions clearly:

- what the stable sample identity is
- which project and paper lineage the row belongs to
- what locality claim is currently supported
- what chronology claim survives review
- which fields later drive country bundles and atlas outputs

In other words, the sample record should tell a reader what this row is before
any map, summary, or country bundle tries to tell a broader story about it.

## Why Projects Do Not Replace Samples

One project accession can contain many samples, and those samples can belong to
different archaeological sites or carry different dates. Treating a project as
if it were already one place or one timeline would flatten the evidence before
it is reviewed.

The public map never outranks the sample database. If a point is visible, the
sample record should already explain why.

## What Readers Can Learn Here

- whether the sample identity is stable or still ambiguous
- whether the record belongs cleanly to one project and paper lineage
- whether later locality or chronology claims are being attached to the right
  sample
- whether a public-facing output is standing on one coherent sample foundation
  or on something still under repair

## Why This Page Matters Publicly

Many downstream misunderstandings start here. If the sample unit is vague, a
reader can be misled before locality, chronology, or coordinates are even
discussed.

That is why the repository keeps the sample record as the durable starting
point instead of letting country bundles or atlas views become the primary
identity surface.

## Direct Files

- `data/adna/governance/animal_sample_foundation_truth.json`
- `data/adna/governance/animal_sample_product_contract.json`
- `data/adna/governance/source_library/project_sample_master_completeness.json`
- `data/adna/governance/source_library/sample_identity_ambiguity_ledger.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_master.json`
- `data/adna/species/ovis_aries/normalized/sample_records.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`

## How To Use This Page Next

- move to [localities](localities.md) if the next question is where the sample
  really belongs
- move to [chronology](chronology.md) if the identity is clear but the dating
  claim is not
- move to [coordinates](coordinates.md) if the real dispute is why the sample
  became a map point
