---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-19
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

## Version Source

Package versions are derived from repository tags through `hatch-vcs`, with a
checked-in fallback for source trees that are not inside a Git tag context.
That keeps local builds, CI builds, and published releases on one versioning
model instead of mixing static file versions with tag-driven publication.

## Release Rule

Do not treat a source refresh as invisible package state. When output-shaping
changes are intentional, the package docs and review trail should explain both
the runtime change and the resulting tracked artifact diff.

## Purpose

This page records the release surfaces that govern package versioning and
publication.
