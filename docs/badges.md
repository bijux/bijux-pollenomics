---
title: Badge Catalog
audience: maintainer
type: reference
status: canonical
owner: bijux-pollenomics-dev
last_reviewed: 2026-04-11
---

# Badge Catalog

`docs/badges.md` is the single source of truth for shared badge templates across
the managed documentation surfaces in this repository. Update the named
templates here, then run `make sync-badges` so the root README, the docs
landing page, the runtime package README, and the maintainer package README
publish the same badge contract.

Do not hand-edit badge blocks inside managed surfaces. Those files consume the
templates below through generated badge sections.

If a page needs product or navigation links outside the managed badge section,
use plain markdown links instead of inline badge markdown.

Generated badge sections always render in this order:

1. surface summary badges when the surface owns them
2. one line of `PyPI` badges for every public package
3. one line of `GHCR` badges for every public package
4. one line of `Documentation` badges for every public package

Link policy for GHCR badges is fixed here as part of the contract:

- the repository-wide GHCR summary badge links to
  `https://github.com/bijux?tab=packages&repo_name=bijux-pollenomics`
- per-package GHCR badges link to the package-specific
  `https://github.com/bijux/bijux-pollenomics/pkgs/container/...` page

## Repository Summary

<!-- bijux-pollenomics-badges:repository-summary:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml?query=branch%3Amain)
[![Release GHCR](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-pollenomics?display_name=tag&label=release)](https://github.com/bijux/bijux-pollenomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-{{ public_package_count }}%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-pollenomics)
[![Published packages](https://img.shields.io/badge/published%20packages-{{ public_package_count }}-2563EB)](https://github.com/bijux/bijux-pollenomics/tree/main/packages)
<!-- bijux-pollenomics-badges:repository-summary:end -->

## Package Summary

<!-- bijux-pollenomics-badges:package-summary:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)]({{ package_pypi_url }})
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml?query=branch%3Amain)
[![Release GHCR](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
<!-- bijux-pollenomics-badges:package-summary:end -->

## Maintainer Summary

<!-- bijux-pollenomics-badges:maintainer-summary:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://github.com/bijux/bijux-pollenomics)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml?query=branch%3Amain)
[![Release GHCR](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
<!-- bijux-pollenomics-badges:maintainer-summary:end -->

## Family PyPI Badge

<!-- bijux-pollenomics-badges:family-pypi-badge:start -->
[![{{ distribution_name }}](https://img.shields.io/pypi/v/{{ distribution_name }}?label={{ pypi_badge_label }}&logo=pypi)]({{ package_pypi_url }})
<!-- bijux-pollenomics-badges:family-pypi-badge:end -->

## Family GHCR Badge

<!-- bijux-pollenomics-badges:family-ghcr-badge:start -->
[![{{ distribution_name }}](https://img.shields.io/badge/{{ pypi_badge_label }}-ghcr-181717?logo=github)]({{ package_ghcr_url }})
<!-- bijux-pollenomics-badges:family-ghcr-badge:end -->

## Family Docs Badge

<!-- bijux-pollenomics-badges:family-docs-badge:start -->
[![{{ docs_badge_alt }}](https://img.shields.io/badge/docs-{{ docs_badge_label }}-2563EB?logo=materialformkdocs&logoColor=white)]({{ docs_url }})
<!-- bijux-pollenomics-badges:family-docs-badge:end -->
