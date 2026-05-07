---
title: Why One Project Can Map To Many Samples
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Why One Project Can Map To Many Samples

One project accession is not one location. A project can contain many samples,
those samples can belong to different archaeological sites, and some of them
can remain unresolved even when other rows from the same project are precise.

## Direct Files

- [`data/adna/governance/source_library/projects/PRJEB36540/sample_master.json`](../../../data/adna/governance/source_library/projects/PRJEB36540/sample_master.json)
- [`data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`](../../../data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json)
- [`data/adna/governance/source_library/project_sample_site_review.json`](../../../data/adna/governance/source_library/project_sample_site_review.json)
- [`data/adna/governance/source_library/sample_site_ambiguity_ledger.json`](../../../data/adna/governance/source_library/sample_site_ambiguity_ledger.json)

## Reader Rule

- start with the project only to find the study bundle
- move to the sample master to count the actual database rows
- read the site table before assuming those samples share one locality
- treat unresolved or region-only rows as blocked geography, not approximate points

This is why the repository publishes sample-owned evidence packets and country
sample queries. They answer the real question: which sample rows justified the
public output, and which rows were held back?
