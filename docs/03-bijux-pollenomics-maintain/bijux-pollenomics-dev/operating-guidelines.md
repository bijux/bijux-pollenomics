---
title: Operating Guidelines
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Operating Guidelines

Maintainer-package changes should narrow ambiguity, not widen it.

## Guidelines

- keep runtime behavior and repository-health behavior in different packages
- prefer small helpers that fail early and explain the failure clearly
- keep checked-in policy artifacts and executable guards aligned
- add or update maintainer docs when a helper changes what the repository
  allows
