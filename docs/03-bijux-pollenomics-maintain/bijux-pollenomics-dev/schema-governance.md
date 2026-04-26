---
title: Schema Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Schema Governance

Schema governance is enforced through checked-in API artifacts and maintainer
helpers.

## Current Anchors

- `apis/bijux-pollenomics/v1/schema.yaml`
- `apis/bijux-pollenomics/v1/pinned_openapi.json`
- `apis/bijux-pollenomics/v1/schema.hash`
- `bijux_pollenomics_dev.api.freeze_contracts`
- `bijux_pollenomics_dev.api.openapi_drift`

## Boundary

The goal is narrow: keep checked-in schema artifacts internally consistent and
make breaking field removals visible. It does not replace broader API design
review.
