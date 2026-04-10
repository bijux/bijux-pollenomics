---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Release and Versioning

The package version and the published scientific outputs are related but not the
same thing.

## Version Anchors

- `__version__` in `bijux_pollenomics/__init__.py`
- package metadata in `packages/bijux-pollenomics/pyproject.toml`
- AADR input version defaults in `config.py`
- `publish.yml` for build, PyPI, GHCR, and GitHub Release publication

## Release Rule

Do not treat a source refresh as invisible package state. When output-shaping
changes are intentional, the package docs and review trail should explain both
the runtime change and the resulting tracked artifact diff.

## Purpose

This page records the versioning surfaces that affect package releases and
review.
