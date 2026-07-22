---
title: Operating Guidelines
audience: maintainer
type: reference
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-07-22
---

# Operating Guidelines

`bijux-pollenomics-dev` turns repository contracts into explicit diagnostics.
It verifies runtime, data, documentation, packaging, and release boundaries
without becoming the owner of their scientific behavior.

## Ownership Test

```mermaid
flowchart TB
    Change{"what decision changes?"}
    Change -->|source, sample, evidence, analysis, publication| Runtime["bijux_pollenomics"]
    Change -->|alias behavior| Alias["pollenomics compatibility facade"]
    Change -->|repository verification or release policy| Toolkit["bijux_pollenomics_dev"]
    Toolkit -. "diagnoses contract" .-> Runtime
    Toolkit -. "diagnoses equivalence" .-> Alias
```

A check belongs in the maintainer package when it evaluates repository state
or policy and can name the owning contract it is checking. Scientific intake,
normalization, evidence fitness, ranking, and publication remain runtime work
even when a maintainer check detects their drift.

## Diagnostic Contract

Every maintainer check should define:

- the governed input it reads;
- the invariant or policy it evaluates;
- whether it is strictly read-only;
- its success and failure exit behavior;
- the evidence retained for diagnosis;
- the runtime, data, documentation, package, or workflow owner responsible for
  correction.

Checks should report the disputed object and contract. A generic failure that
only says the repository is unhealthy creates another ambiguity layer.

## Mutation Boundaries

Maintainer verification is read-only unless a command explicitly owns a
governed synchronization or release artifact. Transient output belongs under
`artifacts/`. Runtime evidence belongs under `data/`; public products belong
under `docs/report/`; shared managed standards are not handwritten downstream.

Do not make a failing check pass by deleting evidence, weakening a claim gate,
ignoring a return code, or teaching the check to accept two conflicting
authorities.

## Check And Synchronize Deliberately

Only badge blocks and package legal-asset copies currently expose maintainer
synchronization modes. Their control flow is explicit:

```mermaid
flowchart LR
    Authority["metadata, badge catalog, or root legal asset"] --> Check["check mode"]
    Check --> Drift{"declared targets differ?"}
    Drift -->|no| Proof["retain focused result"]
    Drift -->|yes| Decide["verify authority and target set"]
    Decide --> Sync["sync mode"]
    Sync --> Review["inspect every written target"]
    Review --> Recheck["check mode"]
    Recheck --> Proof
```

Do not run synchronization as a generic repair. If the authority is wrong,
synchronization distributes the wrong state consistently. Correct the owner
first, then materialize its declared descendants.

`trusted_process` is an execution primitive, not a scope grant. Callers must
assemble arguments without shell expansion, set the working directory and
output destination explicitly, propagate the exit status, and retain enough
diagnostic context to identify the invoked tool.

## Verification Selection

| Changed owner | First maintainer evidence |
| --- | --- |
| public or internal documentation | focused documentation contract and strict site build |
| package identity or alias | package metadata and runtime-equivalence checks |
| API description | schema validation, pinned rendering, and digest agreement |
| repository dependency policy | dependency and lock checks |
| generated public state | owning semantic contract plus reviewed governed diff |
| release posture | package, license, workflow, and repository-truth gates |

Expand verification when the change crosses owners. Do not run broad gates by
habit when a focused contract answers the question, and do not use a focused
check to claim coverage of an unrelated boundary.

## Handoff Record

The maintainer record makes verification reconstructable without private
context:

| Field | Required content |
| --- | --- |
| repository state | branch, base commit, head commit, and whether the worktree is clean |
| changed authority | runtime, data, documentation, package, workflow, or release contract |
| commit boundaries | ordered subjects and the durable intent of each |
| verification | exact command, exit status, pass count, and material warnings |
| omitted proof | broader lane not executed and the scope or cost reason |
| mutations | governed roots, generated targets, or external state changed |
| residual risk | known failure, incomplete evidence, warning, or deferred owner |

Warnings remain visible even when they are expected. A skipped broad gate is
not described as passing. A focused pass is reported only for the contract it
actually exercised.
