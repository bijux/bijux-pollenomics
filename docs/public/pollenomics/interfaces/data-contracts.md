---
title: Data Contracts
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Data Contracts

Most of the runtime contract is visible as files. If a command changes tracked
state, it should do so in governed locations with stable names that a reader or
reviewer can inspect.

This page matters because the repository does not ask readers to trust runtime
behavior in the abstract. It asks them to inspect stable files in stable roots.

## Governing Roots

- `data/` for tracked source and normalized evidence
- `docs/report/` for tracked public report outputs
- `apis/bijux-pollenomics/v1/` for the frozen API contract
- `artifacts/` for transient local output

## What Each Root Means

- `data/` is where source intake, normalized evidence, and review surfaces live
- `docs/report/` is where generated public answers live
- `apis/bijux-pollenomics/v1/` is where the frozen API description lives
- `artifacts/` is for local run products that should not become part of the
  checked-in evidence story

## Contract Rules

- source-family outputs keep their own subtrees rather than collapsing into one
  generic data bucket
- normalized files must remain reviewable without reverse-engineering command
  internals
- downstream publication files must be reproducible from tracked upstream data
- docs pages may explain a contract, but they must not silently replace the
  contract file itself

## Why These Roots Matter

The file layout is part of the public explanation. A reviewer should be able to
see, from the path alone, whether they are looking at source intake,
normalized evidence, downstream publication, or transient local output.

## How To Read The Layout

- if a file is under `data/`, ask what evidence or review responsibility it owns
- if a file is under `docs/report/`, ask what public claim it is making
- if a file is under `artifacts/`, do not treat it as checked-in repository
  truth
- if a docs page claims a contract exists, verify the governing file path
  rather than trusting the prose alone

## Anchor Files

- `data/collection_summary.json`
- `data/adna/governance/animal_sample_foundation_truth.json`
- `docs/report/published_reports_summary.json`
- `docs/report/repository_truth_posture.json`
