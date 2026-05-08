---
title: Runtime System Model
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Runtime System Model

The runtime is easiest to understand as one controlled evidence pipeline. A
user calls a CLI entrypoint, the runtime collects or normalizes tracked files
under `data/`, and the reporting layer turns that state into country bundles,
atlas layers, and review packets under `docs/report/`.

## Execution Path

1. `command_line/` parses operator intent and resolves the durable command
   surface.
2. `data_downloader/` and `adna/` collect, normalize, and validate tracked
   repository state.
3. `reporting/` publishes downstream views from that tracked state.
4. `tests/` and maintainer checks fail when the command, file, and publication
   contracts drift apart.

## Dependency Direction

- `command_line/` depends on runtime modules, never the reverse.
- `data_downloader/` owns source collection and shared normalized file layout.
- `adna/` owns species-aware sample, site, chronology, and coordinate logic.
- `reporting/` depends on tracked data contracts and never invents evidence
  that the upstream repository state does not already justify.
- `foundation/` holds repository-truth and audit builders that describe current
  posture without taking over collection or publication ownership.

## State And Persistence

- tracked source and normalized evidence lives under `data/`
- tracked publication outputs live under `docs/report/`
- docs explain those surfaces but do not replace them
- transient local output belongs under `artifacts/`

## Integration Seams

- `command_line/parsing/subcommands.py` defines the public command surface
- `data_downloader/pipeline/` and `data_downloader/sources/` isolate collection
  and refresh logic by source family
- `adna/` keeps animal evidence recovery separate from pollen, archaeology, and
  boundary context
- `reporting/bundles/` and `reporting/map_document/` isolate country-bundle and
  atlas publication

## Error Model

The runtime should fail early when one of these boundaries breaks:

- a command points at a missing tracked source root
- normalization cannot produce a reviewable tracked artifact
- reporting would publish a surface that has no governed upstream support
- repository-truth checks detect a documentation or evidence overclaim

## Extensibility Posture

The runtime grows by adding durable source-family or publication boundaries,
not by hiding new work inside generic helper buckets. New behavior should name
its domain and governing output clearly enough that a reader can follow it from
command to tracked file to published surface.

## Code Navigation

- start in `packages/bijux-pollenomics/src/bijux_pollenomics/cli.py` when the
  question begins from a command
- start in `packages/bijux-pollenomics/src/bijux_pollenomics/data_downloader/`
  when the question begins from collection or normalization
- start in `packages/bijux-pollenomics/src/bijux_pollenomics/adna/` when the
  question begins from sample-owned evidence recovery
- start in `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/` when
  the question begins from country or atlas publication
