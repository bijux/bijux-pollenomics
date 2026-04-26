---
title: Environment Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Environment Model

The make system centers on one repository-local verification environment.

## Current Anchors

- `artifacts/root/check-venv` as the root check environment
- `UV_PROJECT_ENVIRONMENT` wiring in `makes/root.mk`
- `PYTHONPATH` injection for `packages/bijux-pollenomics-dev/src` when
  maintainer helpers run from root commands
