---
title: Quality Gates
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-07-22
---

# Quality Gates

`bijux-pollenomics-dev` supports repository quality by turning review rules
into executable checks.

## Quality Gate Model

```mermaid
flowchart TB
    policy["review expectations"]
    freeze["api freeze and drift checks"]
    dependency["dependency policy checks"]
    docs["docs and badge integrity"]
    release["license asset alignment"]
    verdict["quality gate verdict"]

    policy --> freeze
    policy --> dependency
    policy --> docs
    policy --> release
    freeze --> verdict
    dependency --> verdict
    docs --> verdict
    release --> verdict
```

These gates are proof surfaces, not chores. Each helper turns one review
expectation into an executable stop condition before repository drift escapes
into broader publication claims.

## Current Gates

- API freeze and schema drift checks
- dependency policy checks
- docs and badge integrity checks
- release support and license alignment checks
- repository truth and publication-claim checks where runtime outputs demand it

## Test Layers

Choose the narrowest layer that owns the risk. Broader execution is warranted
when a change crosses boundaries, not as a substitute for identifying the
affected contract.

| Layer | Location | Use it for |
| --- | --- | --- |
| unit | `tests/unit/` | command parsing, normalization, data layout, geometry, rendering, and other focused behavior |
| regression | `tests/regression/` | tracked repository contracts, documentation conventions, workflow assumptions, and stable artifact expectations |
| end to end | `tests/e2e/` | installed command paths and complete operator-visible effects |

Representative anchors include
`tests/unit/test_command_line.py`, `tests/unit/test_data_layout.py`,
`tests/unit/test_reporting_artifacts.py`,
`tests/regression/test_repository_contracts.py`, and
`tests/e2e/test_cli.py`.

## Select Proof By Changed Boundary

| Changed surface | First proof | Expansion condition |
| --- | --- | --- |
| parser, helper, or normalization rule | owning unit test module | add regression coverage when a tracked contract changes |
| repository or documentation contract | focused regression test | add a strict site build when navigation, links, or rendering can change |
| command wiring or installed behavior | focused end-to-end case | add unit coverage when the defect belongs to an internal rule |
| package metadata or distribution | package check and source-install smoke | add release checks when published metadata changes |
| governed data or report output | owning semantic tests and reviewed artifact diff | add publication checks when membership or exclusions change |

Run unit, regression, and end-to-end suites separately when package test trees
share import names. This keeps collection deterministic and preserves a clear
failure owner. Full gates remain appropriate for release qualification and
genuinely cross-cutting changes.

## Acceptance Record

For each completed change, record the exact checks run, their result, and any
intentionally deferred proof. A passing command is evidence for its owned
boundary; it is not evidence that every repository surface was exercised.
