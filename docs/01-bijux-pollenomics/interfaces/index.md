---
title: Commands and Contracts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Commands and Contracts

The public runtime surface is intentionally small. For most readers it comes
down to three things:

- the commands that rebuild tracked evidence and public outputs
- the artifact families those commands are allowed to write
- the stable Python or CLI entrypoints that outside users can rely on

This section explains those contracts without assuming that the reader already
knows internal helper modules.

## Start Here

- open [CLI surface](cli-surface.md) for command names and examples
- open [entrypoints and examples](entrypoints-and-examples.md) for installed
  command sequences
- open [artifact contracts](artifact-contracts.md) for the checked-in
  publication bundle shape
- open [API surface](api-surface.md) for the durable Python contract boundary
- open [data contracts](data-contracts.md) for the governed roots and file
  locations
- open [operator workflows](operator-workflows.md) for verify, refresh, and
  publication paths
- open [animal ancient DNA evidence](../../02-bijux-pollenomics-data/overview/animal-ancient-dna-evidence.md)
  for the tracked sample, locality, chronology, and coordinate evidence chain
