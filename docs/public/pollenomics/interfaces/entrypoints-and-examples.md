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

This page exists for the shortest supported command paths. It should help a new
reader or operator get to a known-good route quickly, without having to rebuild
the whole repository just to discover the right entrypoint.

## Start With Intent, Not With Commands

Most confusion in this repository comes from choosing a workflow that is wider
than the real question. Start with intent first:

- verify when the question is "is this checkout healthy"
- refresh when the question is "did the tracked evidence change"
- publish when the question is "what public output does the repository now say"
- inspect species-level animal work when the question is narrower than a full
  public rebuild

## Verification Entry Points

```bash
make install
artifacts/root/check-venv/bin/bijux-pollenomics --version
make lock-check
make lint
make test
make test-generated-artifacts
make test-all
make docs
```

Use `make test-generated-artifacts` when the question is specifically about the
governed docs, reports, and other generated-publication contracts. Use
`make test-all` when you want the full local gate instead of the faster default
test slice.

## Collection And Publication Examples

```bash
artifacts/root/check-venv/bin/bijux-pollenomics collect-data all --version v66 --output-root data
artifacts/root/check-venv/bin/bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --context-root data --output-root docs/report
```

These are the shortest canonical routes for rebuilding tracked source material
and tracked public report outputs.

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

## Which Route To Choose

- choose the verification route if you need confidence without rewriting
  tracked repository state
- choose `collect-data` if the goal is source refresh or normalization review
- choose `publish-reports` if the goal is public report and atlas output review
- choose the narrower aDNA commands if the question is species, archive, or
  review specific

## When To Stop

- stop after verification commands if the goal is only repository health
- stop after `collect-data` if the goal is data refresh review
- stop after `publish-reports` if the goal is publication-surface review

That stop rule matters. Many problems in this repository come from running a
much broader workflow than the question actually requires.
