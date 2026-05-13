---
title: Quality Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-05-07
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
