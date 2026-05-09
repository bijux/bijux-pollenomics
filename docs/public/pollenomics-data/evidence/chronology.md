---
title: Chronology
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Chronology

Chronology is tracked at the sample level for the same reason as locality:
one project can contain many rows with different dating strength, different
source wording, and different publication status.

## Direct Files

- `data/adna/governance/source_library/project_sample_chronology_review.json`
- `data/adna/governance/source_library/sample_chronology_normalization_audit.json`
- `data/adna/governance/source_library/sample_chronology_ambiguity_ledger.json`
- `data/adna/governance/source_library/sample_chronology_provenance_review.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_chronology.json`
- `data/adna/governance/source_library/sample_chronology_review.json`
- [`docs/report/animal_sample_chronology_review.md`](../../../report/animal_sample_chronology_review.md)
- [Temporal Semantics](temporal-semantics.md)

## What This Layer Answers

- which rows have normalized intervals or normalized points
- which rows still keep text-only chronology
- which conflicts remain visible and block publication surfaces

Chronology is not an atlas decoration. It is another sample-owned review layer
that determines whether a row can be published cleanly and how much temporal
precision a reader should infer from it.

The newer `sample_chronology_provenance_review` surface adds the missing reader
contract: published wording, the supporting source locator, the normalization
rule, and the uncertainty note for every governed sample chronology row.
