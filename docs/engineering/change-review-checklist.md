---
title: Change Review Checklist
audience: mixed
type: workflow
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Change Review Checklist

Use this checklist when reviewing nontrivial changes to code, data snapshots, or published outputs.

## Source And Data Changes

- can the change be traced back to a specific source refresh, collector fix, or normalization rule
- do raw and normalized artifacts still match each other
- does the changed source behavior stay within the documented provenance contract

## Reporting And Output Changes

- do `docs/report/` changes correspond to code or data changes in the same repository state
- do output docs under `docs/outputs/` still describe the generated artifacts accurately
- if the atlas changed, was `docs/report/nordic-atlas/nordic-atlas_map.html` regenerated intentionally

## Documentation Changes

- do renamed pages keep `mkdocs.yml` and internal links in sync
- do titles, file names, and section names describe durable intent rather than temporary sequencing
- does the page stay honest about limitations instead of implying missing capability already exists

## Verification Changes

- were the relevant commands run for the scope of the change
- if a command was not run, is that gap stated explicitly in the change summary
- if the repo contract changed, were tests or strict docs builds updated to cover it
- if packaging, entrypoints, or automation changed, did the evidence include `make package-verify` or an explicit explanation of why a narrower package command was sufficient

## Purpose

This page records the minimum review questions that keep long-lived repository changes honest and traceable.
