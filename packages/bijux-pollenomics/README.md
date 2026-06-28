# bijux-pollenomics

Runtime package for rebuilding the checked-in `bijux-pollenomics`
pollenomics, environmental, archaeology, boundary, fieldwork, and ancient-DNA
evidence surfaces plus their downstream map/report products.

Use this package when you want the canonical CLI and Python entrypoints that
own tracked source collection, animal aDNA intake, sample extraction,
chronology and coordinate normalization, evidence review, and the atlas plus
country bundles that summarize those reviewable files.

This is the canonical runtime package. Install it when you want the package
that owns the actual collection, review, reporting, and atlas behavior. If you
only want a shorter command name that forwards into the same runtime, install
`pollenomics` instead.

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)

[![bijux-pollenomics](https://img.shields.io/pypi/v/bijux-pollenomics?label=bijux--pollenomics&logo=pypi)](https://pypi.org/project/bijux-pollenomics/)
[![pollenomics](https://img.shields.io/pypi/v/pollenomics?label=pollenomics&logo=pypi)](https://pypi.org/project/pollenomics/)

[![bijux-pollenomics](https://img.shields.io/badge/bijux--pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fbijux-pollenomics)
[![pollenomics](https://img.shields.io/badge/pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fpollenomics)

[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
<!-- bijux-pollenomics-badges:generated:end -->

## Audience

- readers who want the canonical `bijux-pollenomics` command
- maintainers who rebuild `data/` and `docs/report/`
- contributors who need the scientific-logic ownership boundaries inside the runtime package
- readers who need the canonical runtime that keeps pollenomics and
  environmental evidence first-class while treating animal aDNA extraction as
  one still-recovering contextual program
- contributors who need one clear owner for command handling, collection,
  normalization, review, and publication

## Choose This Package When

- you want the canonical `bijux-pollenomics` CLI
- you need the real Python runtime package instead of a compatibility alias
- you are rebuilding tracked data or checked-in report outputs
- you want the package that owns Sweden lake ranking, atlas overlays, and
  report publication behavior

## What This Package Gives You

- the canonical `bijux-pollenomics` CLI
- the Python entrypoints that collect and normalize tracked source data
- the report and atlas publication logic used by the checked-in repository
- the Sweden lake ranking and Nordic atlas overlay surfaces now published from
  the same runtime
- one package-owned boundary document for where runtime logic should live

## Install

```bash
python3.11 -m pip install bijux-pollenomics
bijux-pollenomics --help
```

If you only want the shorter `pollenomics` package name and command, install
the compatibility alias package instead. It forwards into this runtime and does
not own separate scientific logic.

## Read Next

- documentation home: <https://bijux.io/bijux-pollenomics/>
- runtime handbook: <https://bijux.io/bijux-pollenomics/public/pollenomics/>
- animal ancient DNA evidence: <https://bijux.io/bijux-pollenomics/public/pollenomics-data/overview/animal-ancient-dna-evidence/>
- Nordic atlas: <https://bijux.io/bijux-pollenomics/public/nordic-atlas/>
- Sweden lake priorities: <https://bijux.io/bijux-pollenomics/public/nordic-atlas/sweden-lake-priorities/>
- package boundaries: [`docs/boundaries.md`](docs/boundaries.md)
