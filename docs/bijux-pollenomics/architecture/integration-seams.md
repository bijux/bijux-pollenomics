---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Integration Seams

The package integrates across a small set of important seams. Those seams should
stay visible instead of being hidden behind accidental coupling.

## Main Seams

- CLI parsing to runtime handlers
- runtime handlers to `data_downloader` collection workflows
- normalized data outputs to `reporting` bundle assembly
- runtime outputs to tracked docs publication under `docs/report/`
- package code to frozen contracts under `apis/bijux-pollenomics/v1/`

## Why These Seams Matter

These are the points where subtle scope creep appears first. If reporting starts
depending on raw-source quirks or docs start carrying logic that belongs in the
runtime, the package becomes harder to rebuild and harder to review honestly.

## Purpose

This page identifies the high-value seams maintainers should protect.
