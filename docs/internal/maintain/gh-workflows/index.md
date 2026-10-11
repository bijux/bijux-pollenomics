---
title: GitHub Workflows
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-10-11
---

# GitHub Workflows

Human pull requests retain complete configured source admission. Dependabot
proposals receive a bounded review notification without package installation or
product verification. Owners consolidate accepted proposals into a verified
human PR and close superseded proposals after their full changes are covered.
The notification does not approve or automatically merge a dependency change.
The classifier includes Dependabot and `github-actions[bot]` only on the exact
`automation/dependency-lock-refresh` branch; unrelated automation PRs retain
verification.

## Workflow Inventory

| Workflow | Trigger | Responsibility |
| --- | --- | --- |
| `dependency-notice.yml` | Dependabot pull request | A read-only receipt awaiting owner decision |
| `verify.yml` | Human pull request, merge queue, or manual dispatch | Repository contracts, four-package lint/security matrix and successful aggregate |
| `ci.yml` | Reusable call from verification | Complete configured lint and security for one package |
| `github-policy.yml` | Human pull request or merge queue | Managed GitHub state, checksums and pinned actions |
| `pr-approval-policy.yml` | Human PR lifecycle and review events | Owner approval or owner self-signoff enforcement |
| `bijux-std.yml` | Human pull request, merge queue, or manual dispatch | Shared-standard and generated report checks |
| `automerge-pr.yml` | Manual dispatch | Explain owner consolidation; no automatic merging |
| `deploy-docs.yml` | Admitted manual dispatch from main | Build, verify, bundle and deploy the selected accepted revision |
| `release-artifacts.yml` | Reusable call | Build distributions, SBOM and release assets without external publication |
| `release-pypi.yml`, `release-ghcr.yml`, `release-github.yml` | Admitted manual dispatch | Publish the explicitly selected accepted revision and release identity |
| `scientific-verification.yml`, `lra-reference.yml`, `atlas-release-verification.yml` | Manual dispatch | Scientific rebuilds, live reference evidence and browser/deployment verification |

Skipped dependency jobs use distinct `unverified dependency / …` names. Their
notification and skipped checks cannot supply the human required contexts.
Human source admission covers `bijux-pollenomics`, `pollenomics`,
`bijux-pollenomics-dev` and `bijux-pollenomics-lra`. The `verification-ready`
aggregate accepts only successful repository and package results. Scientific
product tests remain separate and are not implied by source admission.

Accepted main merges do not repeat the human PR's complete source checks.
Publication admission binds current main to its exact normally merged human PR
head and requires successful latest Actions contexts. Direct commits, unrelated
old PRs and dependency notices cannot substitute for that evidence. Supported
manifest changes still update GitHub's native dependency graph.

## Generated Workflow Ownership

Canonical verification, policy, deployment and release workflows are generated
by Bijux Std. Repository configuration owns package commands and release
selection; shared execution behavior is corrected upstream and consumed from an
exact accepted GitHub source. Repository-owned scientific/browser workflows
retain their explicit dispatches and budgets.

Interpret each result through its event, exact revision, inputs and retained
outputs. A source check does not establish scientific correctness; a local
strict documentation build does not establish Pages deployment; release assets
do not establish external publication. See [docs deployment](deploy-docs.md)
and [verification and release](verification-and-release.md) for those boundaries.
