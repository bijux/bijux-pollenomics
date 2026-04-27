# bijux-pollenomics

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/workflows/repo%20/%20verify/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://github.com/bijux/bijux-pollenomics/workflows/release-pypi/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://github.com/bijux/bijux-pollenomics/workflows/release-ghcr/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-pollenomics/workflows/release-github/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)

[![bijux-pollenomics](https://img.shields.io/pypi/v/bijux-pollenomics?label=bijux--pollenomics&logo=pypi)](https://pypi.org/project/bijux-pollenomics/)
[![pollenomics](https://img.shields.io/pypi/v/pollenomics?label=pollenomics&logo=pypi)](https://pypi.org/project/pollenomics/)

[![bijux-pollenomics](https://img.shields.io/badge/bijux--pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fbijux-pollenomics)
[![pollenomics](https://img.shields.io/badge/pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fpollenomics)

[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
<!-- bijux-pollenomics-badges:generated:end -->

Runtime package for the bijux-pollenomics repository.

The repository root keeps the long-form documentation, tracked data snapshots, and published report artifacts. This package contains the Python runtime, CLI, and tests that power those repository workflows.

## What This Package Takes And Produces

This package takes tracked source payloads, command inputs, and output-root
destinations. It produces normalized data families under `data/`, checked-in
country bundles under `docs/report/<country>/`, the shared atlas bundle under
`docs/report/nordic-atlas/`, and candidate-site ranking artifacts derived from
the atlas context layers.

Today those candidate outputs are heuristic publication artifacts. They help
review which localities have nearby pollen and archaeological context, but they
do not yet stand in for a full pollenomics analysis runtime.

## What This Package Does Not Yet Do

- genotype-level AADR processing from `.geno`, `.ind`, or `.snp`
- combined eDNA, aDNA, pollen, and archaeological workflow orchestration
- paper-grade statistical scoring for site selection
- automated recommendation engines beyond reviewed atlas-derived artifacts

## Install

`bijux-pollenomics` supports Python 3.11 and newer.

```bash
python3.11 -m pip install bijux-pollenomics
bijux-pollenomics --help
```

If `pip` prints `No matching distribution found` together with messages like
`Requires-Python >=3.11`, run the install command with a Python 3.11+ runtime.

## Read this next

- PyPI package: [bijux-pollenomics on PyPI](https://pypi.org/project/bijux-pollenomics/)
- package guide: [Runtime package docs](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/)
- API surface: [API surface reference](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/api-surface/)
- common workflows: [Operational workflows](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/common-workflows/)
- source directory: [Runtime source directory](https://github.com/bijux/bijux-pollenomics/tree/main/packages/bijux-pollenomics)
- changelog: [Runtime package changelog](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics/CHANGELOG.md)
- security policy: [Security policy](https://github.com/bijux/bijux-pollenomics/blob/main/SECURITY.md)
