---
title: Authoring Rules
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Authoring Rules

New makefiles should keep repository command surfaces understandable years
later.

## Rules

- keep root entrypoints small and durable
- keep package profiles declarative
- avoid copying shared `bijux-py` logic into repository-local files
- add a new target only when its ownership cannot be expressed through an
  existing surface
