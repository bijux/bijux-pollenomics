---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security in `bijux-pollenomics` is mostly about trusted execution and safe
handling of fetched content.

## Current Safety Anchors

- source files are collected through explicit supported-source paths
- XML handling uses `defusedxml`
- repository checks include security and dependency review targets
- tracked outputs make suspicious changes easier to inspect in review

## First Proof Check

- `defusedxml` usage
- collection paths that fetch external content
- tracked output diffs after a refresh
- repository security targets
