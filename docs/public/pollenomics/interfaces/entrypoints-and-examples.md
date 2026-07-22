---
title: Entrypoints and Examples
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Entrypoints and Examples

The installed `bijux-pollenomics` console script is the supported runtime
entrypoint. Commands fall into inspection, validation, collection, evidence
refresh, and publication classes. Choose the narrowest class that answers the
question because only some classes rewrite governed state.

## Discover The Interface

```bash
artifacts/root/check-venv/bin/bijux-pollenomics --version
artifacts/root/check-venv/bin/bijux-pollenomics --help
artifacts/root/check-venv/bin/bijux-pollenomics collect-data --help
```

The examples use the repository installation under
`artifacts/root/check-venv/`. A regular environment can invoke the same console
script as `bijux-pollenomics`.

## Read-Only Inspection

```bash
artifacts/root/check-venv/bin/bijux-pollenomics source-support --json
artifacts/root/check-venv/bin/bijux-pollenomics adna-species
artifacts/root/check-venv/bin/bijux-pollenomics adna-species-review --species ovis_aries --json
artifacts/root/check-venv/bin/bijux-pollenomics adna-runtime-manifest --species ovis_aries --json
```

These commands inspect registered source or species state. They do not perform
a collection or publication refresh.

## Validate A Collection Ledger

```bash
artifacts/root/check-venv/bin/bijux-pollenomics validate-collection-summary \
  --summary-path data/collection_summary.json
```

Validation checks the existing summary and is the appropriate first response
to a summary-contract question.

## Collection And Publication Examples

```bash
artifacts/root/check-venv/bin/bijux-pollenomics collect-data all --version v66 --output-root data
artifacts/root/check-venv/bin/bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
```

`collect-data` writes source-family trees and the collection ledger under
`data/`. `publish-reports` consumes the current governed data state and writes
the world, regional, country, review, and caveat products under `docs/report/`.
Publication does not recollect a source implicitly.

## Atlas And Country Surfaces

```bash
artifacts/root/check-venv/bin/bijux-pollenomics report-country Sweden --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
artifacts/root/check-venv/bin/bijux-pollenomics report-multi-country-map Sweden Norway Finland Denmark --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
```

`report-country` writes one country bundle. `report-multi-country-map` writes a
shared map for the named countries. They are narrower publication operations,
not shortcuts around the same evidence requirements.

## Mutation Boundaries

| Command family | Reads | Writes |
| --- | --- | --- |
| `source-support`, `adna-*` inspection | current governed state | standard output |
| `validate-collection-summary` | one summary file | standard output and exit status |
| `collect-data` | external sources and collector configuration | `data/` |
| `refresh-data-contract-surfaces` | current data tree | collection and contract summaries |
| `publish-reports`, `report-*` | governed data and geography configuration | `docs/report/` |

Inspect the resulting diff after every state-changing command. A successful
exit establishes command completion; the evidence and publication diffs still
require review.
