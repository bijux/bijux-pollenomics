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

Its outputs are repository findings, not scientific observations. A passing
check proves that the inspected contract is internally consistent at that
revision; it does not prove that a source is complete, a chronology is precise,
or a published interpretation is scientifically sufficient.

## Check Contract

```mermaid
flowchart LR
    Governed["repository contract or generated state"] --> Check["maintainer check"]
    Check --> Outcome{"pass or finding"}
    Outcome -->|pass| Proof["focused verification evidence"]
    Outcome -->|finding| ProductOwner["owning runtime, data, docs, or workflow boundary"]
    ProductOwner --> Correction["durable correction"]
    Correction --> Check
```

| Check family | Evidence inspected | Authority limit |
| --- | --- | --- |
| API freeze | canonical schema, pinned representation, and digest | detects drift; runtime API remains product-owned |
| badges and package identity | README badge blocks and release metadata | verifies presentation; does not publish a release |
| repository operations | Make and documentation guidance | verifies routes; Make owners define execution |
| release guards | generated posture and required repository contracts | blocks unsupported release claims; does not strengthen evidence |
| workspace layout | package and governed root boundaries | detects ownership drift; does not redefine package behavior |

A check failure must be corrected at the boundary that owns the disputed fact
or behavior. The maintainer package reports and enforces the mismatch; it does
not create a parallel scientific contract.

## Route Findings To The Owner

| Finding | Correct owner | Typical durable correction |
| --- | --- | --- |
| public API digest drift | canonical runtime API | reconcile the declared API surface and its frozen representation |
| badge or package count mismatch | package and release metadata | correct the governing metadata, then regenerate presentation |
| broken public route or navigation entry | documentation structure | repair the canonical page or navigation contract |
| stale generated report claim | runtime publication or review generator | correct the producer and regenerate the governed report |
| unsupported release language | evidence or release posture | strengthen the underlying evidence or retain the refusal |
| package ownership leakage | owning runtime or maintainer boundary | move behavior to the package that makes the authoritative decision |

Do not satisfy a repository check by weakening the assertion when the
underlying product contract is wrong. The finding is valuable precisely because
it identifies a disagreement between declared and observed state.

## Maintainer Evidence Flow

```mermaid
flowchart LR
    Input["governed repository state"] --> Inspect["focused integrity check"]
    Inspect --> Finding{"contract satisfied?"}
    Finding -->|yes| Evidence["retained verification result"]
    Finding -->|no| Owner["authoritative owning boundary"]
    Owner --> Correction["source, runtime, docs, or release correction"]
    Correction --> Inspect
```

Run the narrowest check that proves the changed contract. Escalate to broader
repository lanes when the change crosses ownership boundaries or when release
evidence requires them.

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
