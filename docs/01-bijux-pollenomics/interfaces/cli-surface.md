---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# CLI Surface

The CLI is the primary public interface for `bijux-pollenomics`. It matters
because these commands rewrite tracked repository state.

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

This page should make the command surface feel bounded and reviewable. The user
is not just invoking helpers; they are choosing one explicit rewrite path
through the repository with visible output consequences.

## Supported Commands

- `collect-data <sources...>` collects tracked datasets into `data/`
- `report-country <country>` publishes one country bundle from AADR metadata
- `report-multi-country-map <countries...>` builds the shared atlas for a
  chosen country set
- `publish-reports` regenerates the checked-in publication bundle set using the
  repository defaults
- `adna-layout --species <name>` prints the canonical species-owned aDNA layout
  under `data/adna/<latin_name>/...`
- `adna-runtime-manifest --species <name>` prints the species-owned runtime
  manifest, including source bundles and analysis boundaries
- `adna-archive-projects` prints the curated ENA project inventory for
  domesticated-animal ancient-DNA intake review, including evidence strength and
  project-level scientific metadata
- `adna-species` prints the canonical ancient-DNA species support matrix and
  current runtime scope
- `adna-species-review --species <name>` prints the governed review for one
  species, including assignment rules, dataset bucket, release blockers,
  project-level admission reviews, and archive integrity
- `surface-map` prints a short runtime-versus-roadmap package surface map
- `product-scope` prints explicit current atlas-builder scope versus not-yet-supported engine claims
- `ownership-map` prints where source-data, ranking, and publication logic live
- `source-support` prints source-family support status and country coverage
- `validate-collection-summary` validates one collected summary payload without rerunning source collection

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
bijux-pollenomics adna-archive-projects --species horse
bijux-pollenomics adna-species
bijux-pollenomics adna-species-review --species horse --json
bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --output-root docs/report --context-root data
```

## First Proof Check

- `src/bijux_pollenomics/cli.py`
- `src/bijux_pollenomics/command_line/parsing/`
- `tests/e2e/test_cli.py`

## Design Pressure

The common failure is to document commands like generic utilities, which hides
that each CLI entrypoint is a controlled path for rewriting tracked evidence or
publication surfaces.
