---
title: gh-workflows
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-20
---

# gh-workflows

This section explains the GitHub Actions entrypoints and reusable building
blocks that verify, release, and document the repository.

Use these pages when you need to know which workflow starts on push, pull
request, tag, or manual dispatch, and how that entrypoint fans out into
repository checks, package jobs, or documentation publication.

The top-level entrypoints are `verify.yml` for pushes and pull requests,
`deploy-docs.yml` for handbook publication from `main`, and split release
workflows for tags: `release-pypi.yml`, `release-ghcr.yml`, and
`release-github.yml`. `release-artifacts.yml` is the reusable build workflow
called by the tag workflows.

Governance automation also includes `automerge-pr.yml`, which enables
auto-merge after trusted CODEOWNERS approval and re-evaluates merge readiness
when required check suites complete.

## Pages In This Section

- [verify](verify.md)
- [release-publication](release-publication.md)
- [deploy-docs](deploy-docs.md)
- [reusable-workflows](reusable-workflows.md)

## Purpose

Use this section to find the workflow file, trigger, and job tree behind a
repository automation concern.
