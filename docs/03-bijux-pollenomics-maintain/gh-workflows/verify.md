---
title: verify
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# verify

`verify.yml` is the main repository verification workflow.

## What It Runs

- a `repository` job that checks shared make and config contracts
- a package matrix for `bijux-pollenomics`, `pollenomics`, and
  `bijux-pollenomics-dev`
- reusable `ci.yml` jobs for package-scoped test, lint, build, SBOM, API, and
  security surfaces

## Trigger Surface

It runs on pushes, pull requests, manual dispatch, and merge groups for changes
that touch workflows, APIs, configs, docs, makes, packages, or core root files
such as `Makefile`, `mkdocs.yml`, `pyproject.toml`, and `uv.lock`.
