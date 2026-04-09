---
title: Change Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Change Validation

Validate changes at the narrowest level that still proves the contract.

## Common Validation Paths

- pure Python logic: unit tests
- output-shape or repository contract changes: regression tests
- command workflow changes: end-to-end CLI tests
- doc structure changes: strict MkDocs build

## Validation Rule

When a change spans code and tracked artifacts, validation is not complete until
both the executable checks and the resulting file diffs make sense together.

## Purpose

This page records how package changes should be validated before merge.
