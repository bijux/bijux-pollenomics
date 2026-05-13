---
title: Verification and Release
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-08
---

# Verification and Release

The workflow tree is the remote enforcement layer for the same repository
contracts that local maintainer commands should check first.

## Verification Surface

- `verify.yml` is the main repository verification workflow
- `ci.yml` and policy workflows keep GitHub-side review expectations aligned
- `deploy-docs.yml` publishes the docs site from the tracked repository state

## Reusable Workflow Pressure

Reusable workflow structure is only useful when it preserves the same contract
names that maintainers can find locally. A reusable layer should reduce drift,
not hide which verification or release rule actually failed.

## Release Surface

- `release-pypi.yml` publishes Python distributions
- `release-ghcr.yml` publishes container artifacts
- `release-github.yml` and `release-artifacts.yml` publish release bundles

## Reusable Expectation

A workflow should expose a repository contract clearly enough that a maintainer
can find the matching local command or package owner without reverse
engineering YAML first.
