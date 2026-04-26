---
title: Package Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Package Contracts

Package profiles under `makes/packages/` declare package identity and enabled
check surfaces while delegating shared implementation to `bijux-py`.

## What The Profiles Declare

- package slug and role
- whether the package is buildable
- whether SBOM and API surfaces are enabled
- where package-scoped make targets should attach
