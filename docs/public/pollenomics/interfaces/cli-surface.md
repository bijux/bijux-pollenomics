---
title: CLI Surface
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# CLI Surface

The `bijux-pollenomics` command is the canonical operational interface. Every
subcommand belongs to collection, evidence inspection, validation, or
publication, and its effect on repository state should be knowable before it
runs.

```mermaid
flowchart LR
    Command["named subcommand"] --> Arguments["validated scope and paths"]
    Arguments --> Handler["owned runtime operation"]
    Handler --> Result{"operation class"}
    Result -->|inspect| Stdout["structured or human-readable output"]
    Result -->|validate| Status["diagnostics and process status"]
    Result -->|write| Files["reviewable tracked artifacts"]
```

## Command Families

| Family | Commands | State effect |
| --- | --- | --- |
| capability and ownership | `surface-map`, `product-scope`, `ownership-map`, `source-support` | read-only orientation |
| animal evidence structure | `adna-layout`, `adna-runtime-manifest`, `adna-artifact-plan`, `adna-curation-manifest`, `adna-normalization-bundle` | read-only manifests and plans |
| animal evidence review | `adna-archive-projects`, `adna-domestication-coverage`, `adna-species`, `adna-species-review`, `adna-release-bar`, `adna-release-readiness` | read-only coverage and release posture |
| validation | `validate-collection-summary` | validates an existing summary without recollection |
| collection and contract refresh | `collect-data`, `refresh-data-contract-surfaces`, `refresh-animal-adna-foundation` | writes governed data and, for the animal refresh, related publication surfaces |
| publication | `report-country`, `report-multi-country-map`, `publish-reports` | writes scoped report and atlas products |

## Command Synopsis

| Form | Result |
| --- | --- |
| `collect-data <sources...>` | collect one or more source families, or `all` |
| `adna-layout --species <name>` | canonical species evidence paths |
| `adna-runtime-manifest --species <name>` | source bundles and analysis boundaries for one species |
| `adna-artifact-plan --species <name>` | deterministic species rebuild paths and governed payloads |
| `adna-curation-manifest --species <name>` | curated, pending, and rejected projects |
| `adna-normalization-bundle --species <name>` | project summaries, study summaries, lineage, and refusals |
| `adna-archive-projects [--species <name>]` | archive inventory and project-side metadata that still needs to feed sample extraction |
| `adna-domestication-coverage` | cross-species curation coverage, including thin and unsupported areas |
| `adna-species` | canonical species identity, support status, and modality matrix |
| `adna-species-review --species <name>` | product role, assignment rule, archive integrity, and project admission reviews |
| `report-country <country>` | one AADR country report bundle |
| `report-multi-country-map <countries...>` | a shared geography surface with country toggles |
| `publish-reports` | the configured world, regional, and country publication tree |

`--output-root` defaults to `data` for collection or `docs/report` for
publication. Commands with additional roots expose them in subcommand help.

## Machine-Readable Inspection

Commands with `--json` expose the same governed result as their table form,
without presentation-oriented line parsing. For example:

```bash
bijux-pollenomics source-support --json
bijux-pollenomics adna-species-review --species "Bos taurus" --json
bijux-pollenomics adna-release-readiness --species "Bos taurus" --json
```

Species arguments accept a registered alias or Latin name. The resolved Latin
name remains the stable identity in evidence paths and result payloads. JSON
output makes the contract automatable, but callers must still interpret status,
refusal, and qualification fields instead of treating record presence as
readiness.

## Inspect Before Materializing

```bash
bijux-pollenomics product-scope
bijux-pollenomics ownership-map
bijux-pollenomics source-support
bijux-pollenomics adna-species
bijux-pollenomics publish-reports --help
```

Help is part of the interface contract. Use subcommand help to confirm required
inputs, default version, country scope, and destination before an operation
that writes files.

## Materialization Boundaries

Collection and publication accept explicit roots so source data and products
can be directed to a known destination:

```bash
bijux-pollenomics collect-data all --version v66 --output-root data
bijux-pollenomics publish-reports \
  --aadr-root data/aadr \
  --version v66 \
  --output-root docs/report \
  --context-root data
```

`collect-data` acquires the selected collector-managed families and updates
their collection state. It may use the network. `publish-reports` reads the
existing AADR and context roots and materializes world, regional, and country
products. It does not collect missing source data.

| Command | Required scope | Primary result | Does not establish |
| --- | --- | --- | --- |
| `collect-data` | one or more source names, or `all` | family captures, normalized data, and collection summary | publication admission |
| `refresh-data-contract-surfaces` | data root and AADR version | collection summary and checked-in contract surfaces | new upstream acquisition |
| `report-country` | one political-entity value | one AADR country report bundle | multi-source regional synthesis |
| `report-multi-country-map` | two or more political-entity values | one shared evidence surface with country toggles | a global or default publication |
| `publish-reports` | country list, data roots, version, and output root | current world, regional, and country publication tree | stronger precision than the inputs provide |
| `refresh-animal-adna-foundation` | species, countries, and governed roots | animal capture, normalized evidence, and dependent animal publications | refresh of collector-managed environmental families |

## Failure Semantics

Argument errors—such as an unknown subcommand, missing required species, or
unsupported source name—fail before the operation runs. Contract and input
errors fail during the owned operation. Successful validation prints the
validated summary path; successful writers print a concise materialization
summary. Callers should rely on the process status and governed artifacts, not
on the presence of an output directory left by an earlier run.

## Alias Command

The `pollenomics` executable is supplied by the compatibility distribution and
forwards to the same runtime with a shorter program name. It does not own
separate handlers, defaults, evidence rules, or report logic. Durable
operational documentation and system ownership use the canonical
`bijux-pollenomics` name.

For Python imports, continue to the [API surface](api-surface.md). For safe
operation sequences, continue to [operator workflows](operator-workflows.md).
