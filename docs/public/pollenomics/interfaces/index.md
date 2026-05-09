---
title: Commands and Contracts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Commands and Contracts

The public runtime surface is intentionally smaller than the full internal
module tree. For most readers it comes down to three things:

- the commands that rebuild tracked evidence and public outputs
- the artifact families those commands are allowed to write
- the stable Python or CLI entrypoints that outside users can rely on

This section explains those contracts without assuming that the reader already
knows internal helper modules. It is here so a reader can tell which parts of
the runtime are meant to be durable and which parts are only implementation
detail.

## Start Here

- open [CLI surface](cli-surface.md) for the named commands readers are
  expected to use
- open [entrypoints and examples](entrypoints-and-examples.md) for the shortest
  supported command paths
- open [artifact contracts](artifact-contracts.md) for the checked-in output
  families the runtime is allowed to write
- open [API surface](api-surface.md) for the durable Python contract boundary
- open [data contracts](data-contracts.md) for the governed roots and file
  locations
- open [operator workflows](operator-workflows.md) for verify, refresh, and
  publication paths
- open [animal ancient DNA evidence](../../pollenomics-data/overview/animal-ancient-dna-evidence.md)
  if your real question is about the evidence chain rather than the command
  surface
