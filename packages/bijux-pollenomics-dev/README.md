# bijux-pollenomics-dev

Maintainer-only package for repository-health checks, docs integrity, and
release support in the `bijux-pollenomics` monorepo.

It is not the owner of runtime commands, source collection, animal aDNA
intake, sample extraction, chronology normalization, coordinate provenance,
evidence review, or atlas publication logic. Those durable scientific
boundaries live in the runtime package.

Use this package when the real question is "is the repository healthy enough to
ship or review?" rather than "how does the scientific runtime work?"

Install it only when you are working on repository checks, release support, or
documentation integrity. Regular users of the runtime should not need this
package.

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://github.com/bijux/bijux-pollenomics)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
<!-- bijux-pollenomics-badges:generated:end -->

## Audience

- maintainers working in the monorepo
- contributors changing docs, release checks, badge sync, or repository truth logic

## Choose This Package When

- you are checking whether the repository is ready to review or release
- you are working on docs integrity, release tooling, or repository truth
  checks
- you need maintainer-facing helpers without pulling scientific ownership into
  a maintainer package

## What This Package Owns

- repository and documentation integrity checks
- release-support helpers and maintainer-facing contract coverage
- badge, handbook, and report-surface verification that should not live in the
  runtime package

## What It Does Not Own

- runtime command handling
- source collection and normalization
- sample truth, chronology, or coordinate provenance
- atlas publication semantics
- scientific ranking logic such as the Sweden lake evidence program

## Read Next

- internal guide: [`docs/internal/index.md`](../../docs/internal/index.md)
- maintainer handbook: [`docs/internal/maintain/index.md`](../../docs/internal/maintain/index.md)
- documentation integrity: [`docs/internal/pollenomics-dev/documentation-integrity.md`](../../docs/internal/pollenomics-dev/documentation-integrity.md)
- release support: [`docs/internal/pollenomics-dev/release-support.md`](../../docs/internal/pollenomics-dev/release-support.md)
