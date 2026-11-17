---
title: Collection Publication
audience: maintainer
type: reference
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-11-17
---

# Collection Publication

`collection.workflow.materialization.staging.collect_into_staging_dir` accepts a
trusted collector callback and returns that callback's original result after its
complete candidate has been attached. Report callbacks use the same core owner
through `reporting.bundles.staging.publish_into_staging_dir`. The collection
workflow does not import the reporting implementation.

Each operation creates an exclusive private candidate and retains its destination
parent authority. A metadata census seals the completed ordinary namespace before
attachment; subsequent growth, aliases, physical substitutions and competing
attachments cause refusal. This is a publication ownership boundary. Collector
content validation and scientific admission remain with their source-specific
owners. Initial callback generation retains its existing uncapped contract; the
completed file and byte counts bound later attachment checks, not earlier work.

Concurrent operations use separate candidates. A competing operation may refuse;
a successful call cannot return one callback's result after attaching another
callback's tree. The shared scope registry supports ordinary joined worker
threads and mixed collection/report nesting. The nearest physical registered
scope takes precedence over a lexical outer scope, including closed or moved
child scopes. Incomplete children prevent outer publication. Private recovery is
kept outside the candidate using the destination-owned, same-filesystem storage
resolver; nested callback operations use the enclosing scope's recovery.

## Recovery And Failures

Before invoking a collector, the workflow refuses any existing legacy
`.name.recovery` entry, including files and dangling links. It never deletes,
adopts or replaces an existing `.name.staging`. The public
`build_staging_output_dir` helper retains its historical naming behavior for
source-specific consumers; it does not identify the callback owner's private
candidate. The standalone `reset_output_dir` utility remains an explicit removal
operation and is not used by callback publication.

Refused private candidates and displaced predecessors remain available for
review. Error notes identify their original recovery path and expected directory
identity; verify the current physical attachment before using that path. Cleanup
must preserve the callback's original failure, including cancellation. Neither a
foreign final nor a foreign recovery entry is removed to make a losing operation
succeed. As with the existing core replacement primitive, boundary identity
checks do not claim an operating-system inode compare-and-swap guarantee.

## Replacement Metadata

`SourceReplacementRule` keeps its existing constructor field order and fields.
The `staging_output_root` field accepts either text or null:

| Mode | Staging path | Meaning |
| --- | --- | --- |
| `staging_swap` | historical fixed sibling path | Preserve the recorded source-specific rule as written. |
| `owned_callback_replacement` | null | A private candidate is allocated at runtime; there is no fixed planning-time path. |

Historical string-valued rules remain readable and serialize without conversion.
Do not reinterpret an old report according to a newer implementation. Consumers
of the new mode must handle its explicitly absent planning-time staging path;
constructing a filesystem path from null is unsupported. `destructive_refresh`
means the governed destination is replaced, while failure recovery and retained
private predecessors remain separate responsibilities.

The catalog follows the actual workflow routes. AADR and boundaries use explicit
callback branches. Context sources with `owns_output_publication=False` use the
shared callback owner: LandClim, RAA, SEAD and SVAR. Neotoma declares its own
publication owner and retains its separate fixed-stage rule. This contract does
not qualify or replace Neotoma's source-specific capture, capsule or publication
protocols.

Collector return values are preserved rather than rewritten. Paths inside those
values refer to the callback's own execution namespace unless the collector
contract states otherwise. Workflow count aggregation consumes the declared
counts; source manifests retain their source-specific relative member semantics.
A completed filesystem publication does not establish retained-source coverage,
scientific correctness, or permission to acquire additional inputs.
