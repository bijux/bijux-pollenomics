---
title: gh-workflows
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# gh-workflows

Open this section when you need the GitHub Actions entrypoints and reusable
building blocks that verify, release, and document the repository.

Open these pages when you need to know which workflow starts on push, pull
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

## Start Here

- open [verify](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/verify/) when the question begins with a push, pull request,
  or required-check failure
- open [release-publication](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/release-publication/) when a tag or published
  artifact did not behave as expected
- open [deploy-docs](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/deploy-docs/) when handbook publication from `main`
  failed or produced stale output
- open [reusable-workflows](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/reusable-workflows/) when the visible entrypoint
  fans out into shared build jobs

## Pages In This Section

- [verify](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/verify/)
- [release-publication](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/release-publication/)
- [deploy-docs](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/deploy-docs/)
- [reusable-workflows](https://bijux.io/bijux-pollenomics/03-bijux-pollenomics-maintain/gh-workflows/reusable-workflows/)

## Open This Section When

- you need to map a repository event to the workflow file that owns it
- the failure appears in GitHub Actions rather than in a local Make invocation
- you need to know whether automation is an entry workflow, a reusable job, or
  governance-only behavior

## Open Another Section When

- the real question is which local or CI Make target should be run
- the problem is inside package code, data normalization, or atlas behavior
- you are looking for end-user product docs rather than repository automation

## Bottom Line

Open `gh-workflows/` when the issue starts with a GitHub event, a check suite,
or a release trigger. The point of this section is to identify the automation
owner quickly, then hand you off to the exact workflow page instead of making
you reverse-engineer YAML from the repository root.
