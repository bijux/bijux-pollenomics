---
title: Neotoma Source Publication
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-11-16
---

# Neotoma Source Publication

The host package publishes download archives with
`collection.sources.neotoma.collection.write_neotoma_download_archive` and
relational snapshots with
`collection.sources.neotoma.materialization.materialize_neotoma_relational_snapshot`.
Both functions validate a complete candidate before replacing the destination.
Their publication receipts describe filesystem custody; scientific admission
belongs to the source and method input contracts.

## Ownership And Recovery

Existing output must satisfy the corresponding complete archive or relational
contract before replacement. A familiar filename alone does not establish
ownership. Candidate writes remain attached to the directory created by the
publisher. Stage validation, final attachment checks and exact readback must
succeed before the function returns.

A successful replacement retains its predecessor. A failed publication retains
its candidate and recovery state. Competing foreign entries are preserved;
rollback restores a predecessor only when its destination is absent. An error
note identifies retained recovery state. A secondary refusal-receipt error is
attached to the original exception rather than replacing that failure.

The destination determines recovery placement:

- A recognized Pollenomics repository uses
  `artifacts/neotoma-publication/` for receipts and, on the same filesystem,
  recovery trees.
- A destination on another filesystem retains its recovery tree beside the
  destination, with receipts in the owning repository.
- A standalone destination uses an exclusive private
  `.neotoma-recovery-…` directory beside the destination for recovery and receipts.

Repository ownership comes from the destination's nearest project boundary.
An unrelated or malformed nearer project marker prevents borrowing an outer
repository. The installed module's location does not choose recovery storage.
For an identical absolute destination, changing the caller's working directory
does not redirect recovery into that directory.

Keep retained trees and receipts together when investigating a refusal. Recovery
retention has no automatic lifetime or disk-quota guarantee.

## Finite Read And Write Profiles

| Product | Complete tree byte ceiling | File ceiling | Manifest read ceiling |
| --- | ---: | ---: | ---: |
| download archive | 512 MiB | 20,000 | 16 MiB |
| relational materialization | 640 MiB | 20,000 | 16 MiB |

The relational profile accommodates the recorded materialization independently
of the raw archive profile. These limits bound selected ordinary files and
candidate output; they do not bound peak memory, cumulative read traffic or
all retained recovery trees. Both formats refuse aliases, unsuitable file
types, source growth beyond the selected bound and changes to sealed inputs.

The shared `core.http.fetch_text` and `fetch_json` transports, including
`collection.sources.neotoma.client.fetch_neotoma_json`, default to a 32 MiB
response limit and a 30-second socket timeout. `timeout=None` selects that finite
default. Larger source responses require an explicit positive `max_bytes`;
text and JSON limits apply to received bytes before UTF-8 decoding. Declared
oversize responses refuse before a body read; observed overflow consumes at
most one additional sentinel byte. Refusals and HTTP errors close their response
streams, and a secondary close failure cannot replace the original error.

Socket timeouts do not bound a complete multi-request collection. The existing
three-attempt transport budget applies to each invocation; callers that retry
an invocation need a separate operation request budget. The ancestry frontier
producer uses its own stricter two-MiB, one-attempt profile.

The replacement contract preserves owned and competing trees during handled
failures. It does not promise process-crash atomicity or an atomic comparison
of a source pathname's inode against a competing writer.

## Verify Installed Behavior

Build the host and LRA wheel and source distribution from one clean, recorded
commit. Install each route into a fresh environment, use an isolated Python
interpreter without a source `PYTHONPATH`, and check dependency consistency.
Verify installed payload bytes against the built distributions and exercise
cold imports in separate processes; a prior import can hide a dependency cycle.

Use generated records to test repeated archive and relational publication,
retained predecessors, write failures and foreign candidate substitution. Change
the caller's directory while keeping the absolute destination fixed. Check
actual receipts and final bytes, rather than substituting a source-tree module
path to simulate installation. These controls qualify software behavior without
requiring retained scientific observations.

The separately published [portable native source archive](../../../public/pollenomics-data/sources/neotoma-source-resources.md)
has its own manifest, population and selected-reader contract. Installing the
host package does not install that archive or admit its data to LRA.

## Retained Observation Checks

The retained observation trace test is skipped by default. Enabling
`BIJUX_POLLENOMICS_NEOTOMA_OBSERVATION_SOURCE_CHECK=1` reads the complete raw
`part-001.json` and relational observations `part-00002.json`, even though its
assertions follow one observation. Review the exposure scope of both complete
partitions before enabling it; a single asserted sample does not bound the
observations decoded by the test. A passing trace does not establish an untouched
validation cohort.

The separate original BOKE occurrence check retains its existing
`BIJUX_POLLENOMICS_NEOTOMA_BOKE_OCCURRENCE_CHECK` opt-in. Neither opt-in is needed
for generated archive, relational publication or evidence-session controls.

## Ancestry Source Qualification

The [recorded taxonomy source qualification](../../../../reports/science/source-cohorts/neotoma-taxonomy-source-qualification.json)
binds one offline maintained derivation to an exact source revision and its
complete input closure: 236 roots, 34,310 files and 2,735 previously received
entities. The result matches the existing twelve-file ancestry baseline.
No new source request or governed data write occurred.

This qualifies replay of the retained source projection. It does not publish
its complete portable dependency capsule or establish scientific admission.
The selected-target reader returns recorded metadata; it does not independently
revalidate current permissions or authorize native-body access or collection.
