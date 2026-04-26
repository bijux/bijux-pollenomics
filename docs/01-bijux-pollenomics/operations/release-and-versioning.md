---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The package version and published scientific outputs are related but not the
same artifact boundary.

## Version Anchors

- `tool.hatch.version` in `packages/bijux-pollenomics/pyproject.toml`
- installed package metadata resolved by `importlib.metadata`
- AADR input version defaults in `config.py`
- split release workflows:
  `release-artifacts.yml`, `release-pypi.yml`, `release-ghcr.yml`,
  and `release-github.yml`

## First Proof Check

- `packages/bijux-pollenomics/pyproject.toml`
- `config.py`
- `.github/workflows/release-*.yml`
- `.github/workflows/deploy-docs.yml`
