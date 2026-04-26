---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility in `bijux-pollenomics` is about preserving rebuildability and
review clarity, not only preserving Python import names.

## Current Commitments

- documented CLI commands remain named and scoped consistently
- default output roots and stable slugs change only deliberately
- frozen API contracts under `apis/bijux-pollenomics/v1/` stay synchronized with
  implementation
- tracked data and report layout changes are documented when they are
  intentional

## Known Non-Commitments

- upstream source services are not guaranteed stable by this package
- unpublished internal module names may change during refactors

## First Proof Check

- `tests/e2e/test_cli.py`
- `tests/unit/test_config.py`
- `tests/regression/test_repository_contracts.py`
- `apis/bijux-pollenomics/v1/`
