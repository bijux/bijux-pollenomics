---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

The package architecture is intentionally simple, but its main risks are not
equal. The worst failures are the ones that damage trust in tracked outputs or
blur the line between collection, publication, and adjacent repository
surfaces.

## Current Risks

- tracked file outputs can make small code changes look large in review
- upstream source changes can pressure the package into source-specific special
  cases that leak across the runtime
- report rendering and data collection both touch durable files, so boundary
  drift between them is costly
- docs can lag behind package behavior if output contracts change without a
  matching handbook update

## Higher-Risk Failures

- output-path or slug renames that force wide downstream change
- source-specific special cases that leak across the runtime
- collection and reporting boundary drift around durable files
- docs lagging behind contract changes in visible publication surfaces

## First Proof Check

- `tests/regression/test_repository_contracts.py`
- `tests/regression/test_data_collector.py`
- `tests/regression/test_country_report.py`
