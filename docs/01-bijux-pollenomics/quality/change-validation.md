---
title: Change Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Change Validation

Validate changes at the narrowest level that still proves the contract.

## Common Validation Paths

- pure Python logic: unit tests
- output-shape or repository contract changes: regression tests
- command workflow changes: end-to-end CLI tests
- doc structure changes: strict MkDocs build

## First Proof Check

- unit tests for local logic changes
- regression tests for tracked output or repository-contract changes
- end-to-end CLI tests for workflow changes
- strict docs build for docs structure changes
