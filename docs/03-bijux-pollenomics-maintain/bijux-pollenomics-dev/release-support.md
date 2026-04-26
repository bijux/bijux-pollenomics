---
title: Release Support
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Release Support

The maintainer package keeps release safety checks close to the repository.

## Current Release Surfaces

- `release/version_resolver.py` resolves package versions from metadata, Hatch,
  or tags
- `release/publication_guard.py` blocks prerelease, dirty, or mismatched
  artifact publication unless explicitly allowed
- `release/license_assets.py` syncs root license assets into package trees

## Boundary

These helpers protect release correctness. They do not perform the full release
workflow by themselves; Make and GitHub Actions call into them.
