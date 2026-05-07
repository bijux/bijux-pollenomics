---
title: CLI Surface
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# CLI Surface

The CLI is the primary runtime interface because it rewrites tracked repository
state.

## CLI Model

```mermaid
flowchart TB
    command["named CLI command"]
    options["shared options and defaults"]
    handler["runtime handler"]
    outputs["tracked data, report outputs, or typed runtime review"]
    review["reviewable repository change"]

    command --> options
    options --> handler
    handler --> outputs
    outputs --> review
```

The point of this page is not to list every internal helper. It is to make the
reviewable command surface explicit.

## Supported Commands

- `collect-data <sources...>` collects tracked datasets into `data/`
- `report-country <country>` publishes one country bundle from AADR metadata
- `report-multi-country-map <countries...>` builds the shared atlas for a
  chosen country set
- `publish-reports` regenerates the checked-in publication bundle set using the
  repository defaults
- `adna-layout --species <name>` prints the canonical species-owned aDNA layout
  under `data/adna/species/<latin_name>/...`
- `adna-runtime-manifest --species <name>` prints the species-owned runtime
  manifest, including source bundles and analysis boundaries
- `adna-artifact-plan --species <name>` prints the deterministic species rebuild
  artifact plan, including governed manifest and review payload paths
- `adna-curation-manifest --species <name>` prints the governed curation
  manifest for one species, including curated, pending, and rejected projects
- `adna-normalization-bundle --species <name>` prints the governed non-human
  normalization bundle, including project summaries, study summaries, lineage,
  and explicit refusals
- `adna-archive-projects` prints the curated ENA project inventory for
  domesticated-animal ancient-DNA intake review, including evidence strength and
  the current project-side metadata that still needs to feed sample extraction
- `adna-domestication-coverage` prints the cross-species curation coverage
  report, including support class and honesty posture for each domestication
  program species
- `adna-species` prints the canonical ancient-DNA species support matrix and
  current runtime scope
- `adna-species-review --species <name>` prints the governed review for one
  species, including assignment rules, dataset bucket, release blockers,
  project admission reviews, sample-foundation blockers, and archive integrity
- `surface-map` prints a short runtime-versus-roadmap package surface map
- `product-scope` prints explicit current atlas-builder scope versus not-yet-supported engine claims
- `ownership-map` prints where source-data, ranking, and publication logic live
- `source-support` prints source-family support status and country coverage
- `validate-collection-summary` validates one collected summary payload without rerunning source collection

The commands that matter most for readers are `collect-data`, `report-country`,
`report-multi-country-map`, and `publish-reports`. The rest are evidence and
contract inspection commands that explain how one species surface is shaped.

## Shared Options

- `--version` selects the AADR version directory and defaults to `v66`
- `--aadr-root` defaults to `data/aadr`
- `--output-root` defaults to `data` for collection or `docs/report` for
  report publishing
- `--context-root` defaults to `data`
- `--name` and `--title` control the atlas slug and display title

## Example

```bash
bijux-pollenomics collect-data all --version v66 --output-root data
bijux-pollenomics adna-layout --species horse
bijux-pollenomics adna-runtime-manifest --species "Homo sapiens" --version v66
bijux-pollenomics adna-artifact-plan --species horse
bijux-pollenomics adna-curation-manifest --species horse
bijux-pollenomics adna-normalization-bundle --species horse --json
bijux-pollenomics adna-archive-projects --species horse
bijux-pollenomics adna-domestication-coverage --json
bijux-pollenomics adna-species
bijux-pollenomics adna-species-review --species horse --json
bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --output-root docs/report --context-root data
```

## First Proof Check

- `src/bijux_pollenomics/cli.py`
- `src/bijux_pollenomics/command_line/parsing/`
- `tests/e2e/test_cli.py`
