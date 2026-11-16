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
