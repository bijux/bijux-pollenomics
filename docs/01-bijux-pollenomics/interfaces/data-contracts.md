---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Data Contracts

The package's data contracts are filesystem contracts.

## Contracted Shapes

- each supported source owns a stable subtree under `data/<source>/`
- raw and normalized outputs are separated so source fidelity and repository
  friendliness are both inspectable
- collection summaries and source-specific normalized outputs must remain
  reproducible from one repository state

## Key Contract Modules

- `data_downloader/contracts.py`
- `data_downloader/data_layout.py`
- `data_downloader/pipeline/summary_writer.py`

## Migration Warning

Renaming source directories or normalized filenames is a high-friction change.
It ripples into docs, report publishing, tests, and reviewer expectations.

## Purpose

This page explains the package's stable contracts for tracked data outputs.
