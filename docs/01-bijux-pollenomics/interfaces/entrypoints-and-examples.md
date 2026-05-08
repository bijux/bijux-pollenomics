---
title: Entrypoints and Examples
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Entrypoints and Examples

Use the installed console script, not `python -m`, when you want the canonical
runtime surface.

## Verification Entry Points

```bash
make install
artifacts/root/check-venv/bin/bijux-pollenomics --version
make lock-check
make lint
make test
make docs
```

## Collection And Publication Examples

```bash
artifacts/root/check-venv/bin/bijux-pollenomics collect-data all --version v66 --output-root data
artifacts/root/check-venv/bin/bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
```

## Narrow aDNA Surfaces

```bash
artifacts/root/check-venv/bin/bijux-pollenomics adna-archive-projects
artifacts/root/check-venv/bin/bijux-pollenomics adna-domestication-coverage
artifacts/root/check-venv/bin/bijux-pollenomics adna-species
artifacts/root/check-venv/bin/bijux-pollenomics adna-species-review --species ovis_aries
```

## Atlas And Country Surfaces

```bash
artifacts/root/check-venv/bin/bijux-pollenomics report-country Sweden --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
artifacts/root/check-venv/bin/bijux-pollenomics report-multi-country-map Sweden Norway Finland Denmark --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
```

## When To Stop

- stop after verification commands if the goal is only repository health
- stop after `collect-data` if the goal is data refresh review
- stop after `publish-reports` if the goal is publication-surface review
