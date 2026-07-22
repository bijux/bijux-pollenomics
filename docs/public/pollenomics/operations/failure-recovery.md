---
title: Failure Recovery
audience: reader
type: how-to
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Failure Recovery

Recovery begins by identifying the last coherent governed state. Retrying a
broad workflow before that boundary is known can enlarge the diff, obscure the
cause, and make partial output look authoritative.

## Locate The Failed Boundary

| Symptom | Likely boundary | State to inspect |
| --- | --- | --- |
| command rejected arguments | parsing or precondition | no governed write should have occurred |
| source capture failed | network, identity, license, or upstream format | staged capture and prior governed family tree |
| normalization failed | source semantics or schema | raw capture, normalized staging, and review findings |
| contract refresh failed | inconsistent governed tree | collection summary and family contracts |
| publication failed | admission, scope, traceability, or rendering | publication staging and previous `docs/report/` tree |
| claim gate refused output | evidence or language exceeded the declared contract | refusal, exclusion, readiness, and truth-posture records |

```mermaid
stateDiagram-v2
    [*] --> Prior: prior governed state
    Prior --> Staging: begin state-changing work
    Staging --> Rejected: acquisition or validation fails
    Rejected --> Prior: discard incomplete staging
    Staging --> Accepted: complete boundary passes
    Accepted --> Governed: replace owned tree
    Governed --> [*]
```

Collectors and publishers use staging so a failed boundary can preserve the
previous governed tree. Confirm that preservation explicitly; do not infer it
from a single successful log line.

## Recovery Procedure

1. Stop at the first failed boundary.
2. Preserve the error and transient diagnostics under `artifacts/`.
3. Inspect tracked changes only within the operation's declared write root.
4. Compare the current tree with the last coherent manifest, hashes, counts,
   and membership.
5. Correct the owning source, contract, evidence decision, or publication rule.
6. Rerun the narrow operation and review its complete output before expanding
   scope.

## Scientific Failure Modes

Some failures are valid evidence outcomes rather than software defects:

- a paper is known but its sample-bearing supplement is unavailable;
- a project is recoverable but a sample cannot be linked to a named site;
- chronology exists only at project level;
- a coordinate is too broad for exact-point publication;
- a contextual source cannot support the direct claim requested;
- a known candidate falls outside the product's geographic or evidence scope.

Preserve these states as qualified records, recovery work, or reasoned
exclusions. Replacing them with inferred values would make the workflow appear
successful by weakening the evidence.

## When A Broader Rebuild Is Safe

A broader rebuild is appropriate after the failed owner is understood, the
previous governed state is confirmed, and the narrow operation produces a
coherent reviewable diff. It is not a recovery mechanism for uncertainty about
which boundary failed.
