---
title: Automation Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-09
---

# Automation Workflows

The repository uses three repository-facing GitHub Actions workflows plus two reusable workflow primitives:

- `verify.yml` runs repository contracts plus package verification on pushes to `main`, pull requests targeting `main`, and manual dispatch
- `publish.yml` builds and publishes the release distribution from the shared `v*` tag contract or manual dispatch
- `deploy-docs.yml` builds the MkDocs site from `main` or manual dispatch and publishes the rendered site into the dedicated `bijux/pollenomics` Pages repository
- `ci-package.yml` is the reusable package verification primitive used by `verify.yml`
- `build-release-artifacts.yml` is the reusable release-build primitive used by `publish.yml`

The workflow names are only useful if the responsibility split stays explicit.

## Verification Workflow

`verify.yml` is the main repository guardrail in GitHub.

It:

- checks out the repository
- installs Python 3.11
- installs `uv` with cache support
- runs repository layout and shared-make contract checks
- runs `make check PYTHON=python`
- fails if `make check` leaves tracked or untracked repository drift behind
- runs package-level verification through the reusable `ci-package.yml` matrix for both `bijux-pollenomics` and `bijux-pollenomics-dev`

That means GitHub verification now covers:

- lockfile validity
- lint
- unit, regression, and end-to-end tests
- strict MkDocs builds
- source and wheel metadata validation
- temporary-environment wheel smoke installation

The clean-worktree check matters because it proves the verification path is not quietly leaving behind generated drift.

## Publish Workflow

`publish.yml` publishes release artifacts and serves as the release entrypoint for the repository.

It:

- reuses `build-release-artifacts.yml` to build the distribution from the package-scoped make entrypoint
- stages wheel and source distribution artifacts from the package release output
- uploads the release artifact bundle for review
- publishes the staged distribution through the PyPI action using `PYPI_API_TOKEN`

This keeps release build logic reusable while exposing only one public publish entrypoint.

## Docs Deployment Workflow

`deploy-docs.yml` is intentionally narrower than the verification workflow.

It:

- validates core MkDocs contract fields in `mkdocs.yml`
- builds the docs site into `artifacts/root/docs/site`
- verifies that the build published the browser-probed root icons into the site root
- publishes that built site into the `bijux/pollenomics` repository when the ref is `refs/heads/main`
- requires a `POLLENOMICS_PUBLISH_TOKEN` secret with write access to `bijux/pollenomics`

It does not publish from tags, and it does not pretend to be the whole repository test suite.

## Separation Rule

Keep verification and publication separate:

- verification proves that the repository state is coherent
- docs deployment publishes one checked-in surface derived from that state

If a future automation change mixes those responsibilities, document the new boundary explicitly instead of relying on workflow names alone.

## Purpose

This page records the intended GitHub automation contract for the repository.
