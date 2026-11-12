# Contributing

This repository publishes multiple packages, but it should still feel like one
coherent system. Good contributions improve a package without weakening the
shared contracts that keep the rest of the workspace aligned.

## Start With Placement

Choose the narrowest correct home for every change:

- package runtime behavior belongs in the owning package under `packages/`
- repository-wide automation belongs in `makes/`
- shared tool policy belongs in `configs/`
- checked-in API contracts belong in the repository API contract directory
- repository governance and handbook content belong at the root or in `docs/`

If the same rule would need to be copied into multiple packages, that is a sign
it probably belongs at the repository level instead.

## Working Principles

- prefer one shared fix over many package-local copies
- keep generated outputs under `artifacts/`
- keep names durable and descriptive rather than tied to temporary planning
  language
- write docs for humans first, especially in the root handbook
- preserve compatibility shims only where they still serve a migration purpose

## Local Workflow

1. Read the root handbook entry points in `README.md` and `docs/`.
2. Change the smallest surface that can honestly own the behavior.
3. Run the checks that match the area you touched.
4. Update contracts, docs, or metadata when the change affects shared behavior.
5. Commit in a small, coherent step with a durable message.

## Validation Expectations

Use the generated root help to discover the current command surface:

- `make help`
- `make list`
- `make list-all`

Typical validation flows:

- root docs and governance changes: `make docs-check`
- root workflow or config changes: `make help`, `make list-all`, and any
  relevant package or root targets
- package-scoped changes: `make -C packages/<package> <target>`
- repository package dispatch changes: `make <target> PACKAGE=<package>`

If you touch checked-in API contracts, schemas, or publish flows, verify the
resulting artifacts rather than assuming the repository state stayed
consistent.

## Commits

Use Conventional Commits with clear, durable intent.

Good examples:

- `build(repo): centralize pytest configuration`
- `docs(governance): clarify repository security reporting`
- `refactor(ci): replace duplicated package workflow wiring`

Avoid commit messages that depend on temporary project language or internal
iteration labels. Someone reading the history two years later should still know
what changed and why.

## Pull Request Quality Bar

- explain the user-facing or maintainer-facing effect
- call out compatibility impact when behavior or naming changed
- mention any follow-up that still remains open
- keep unrelated edits out of the same change

## Change History

Include a root `CHANGELOG.md` entry in every pull request. Prepare it alongside
the change, add the actual PR number and link once the PR exists, and finish it
before merge. Do not collect several merged PRs into a later changelog refresh.

Use one level-three heading per PR: a linked PR number followed by a short,
descriptive title. Keep merged entries newest merge first; PR numbers alone do
not establish merge order. An open PR uses its actual link without claiming a
merge date or adding a status label that will become stale after merge.

Cover every meaningful outcome in the PR, including package behavior,
scientific methods and data, reports, presentation, documentation, dependencies,
and delivery tooling where affected. Group related changes into readable
bullets; a large PR needs more than a restatement of its title. Describe the
result and important limits instead of listing commits, hashes, files, or test
logs. Scientific qualifications must retain their scope: synthetic or retained
evidence does not establish field accuracy or independent scientific approval.
State material negative results, refusals and deferred verification alongside
the delivered capability.

Before merge, compare the entry with the complete final PR diff and revise it
when scope changes. Fold follow-up commits into the same entry. Describe
already-present changes, combined proposals and restored history explicitly;
do not credit the same feature twice or use a PR title as proof of its contents.

The root changelog records repository progress across all packages. Package
changelogs retain distribution release notes. Neither a merged PR nor prepared
release notes prove that a package, website, or scientific result was published.

## When Shared Files Move

If you move or rename root-owned files, update the references that point to
them:

- package metadata and URLs
- workflow paths and automation
- docs links and handbook navigation
- contract or release references

## Getting Help

Open an issue for questions that are not security-sensitive. For security
issues, use the private reporting guidance in `SECURITY.md`.
