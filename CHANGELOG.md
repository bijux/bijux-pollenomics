# Changelog

This file records notable repository-level changes for `bijux-pollenomics`.

It does not replace package-level release history. Versioning and package-local
release notes belong to each distribution under `packages/`.

Use this changelog for workspace changes that affect multiple packages or
change contributor and maintainer workflows across the repository.

## 0.1.3 - 2026-04-16

### Changed

- Repository defaults and generated outputs now align on AADR `v66`, including
  tracked source snapshots under `data/aadr/` and regenerated report bundles
  under `docs/report/`.
- Shared repository directories now comply with `bijux-std v0.1.0`, including
  synchronized `shared/bijux-docs`, `shared/bijux-makes-py`, and
  `shared/bijux-checks` standards.
- Shared atlas output now labels the AADR evidence layer with its active
  release version, for example `AADR-v66 aDNA samples`.
- Workspace release and publish automation now include both distribution names,
  `bijux-pollenomics` and the `pollenomics` compatibility alias.

### Fixed

- AADR release resolution now accepts current Dataverse naming formats used by
  `v66` files, preventing missed `.anno` selection during collection.
- Report generation now accepts the current AADR schema header variants, so
  `publish-reports` succeeds against `v66` source files.
- Shared README badge sync now covers the compatibility package, keeping
  package-map status links consistent across both published distributions.
- Release security gates now use `pytest>=9.0.3` where dev-tooling dependencies
  are defined, addressing the pip-audit advisory for `pytest 8.4.2`.
- Package build metadata now resolves license files from package-local sources
  so sdist install-smoke checks work from isolated build environments.
- Packaging verification now cleans stale artifacts before each build and runs
  smoke installs against dependency-complete environments using the current
  `artifacts/bijux-pollenomics/build` output path.
- License metadata now follows a root-source model: package `LICENSE` and
  `NOTICE` files are synchronized from repository root automation before checks
  and package builds.

## 0.1.2 - 2026-04-11

### Changed

- Root README package-map links now render PyPI, docs, GHCR, and source as
  badge links, matching the shared Bijux repository style.
- Repository, package, and source-checkout fallback versions now align with the
  synchronized `v0.1.2` pollenomics release line.

## 0.1.1 - 2026-04-10

### Changed

- Tag-derived fallback versions now align with the synchronized `v0.1.1`
  pollenomics release line.
- Source-checkout version fallbacks and command-line version checks now target
  `0.1.1` as the current package release version.

## 0.1.0 - 2026-04-10

### Added

- A unified repository automation layout now exists under `makes/`, including
  stable root entrypoints, package profiles, and a shared `bijux-py` make
  series aligned with sibling Bijux repositories.
- A centralized repository configuration tree now exists under `configs/`,
  giving the workspace one durable source for Ruff, mypy, pytest, coverage,
  deptry, and API-contract settings.
- Root governance and contributor files now exist in the same style as the
  sibling repositories, including aligned `LICENSE`, `NOTICE`,
  `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `SECURITY.md`.
- Repository-wide make handbooks now explain layout boundaries, ownership
  rules, and extension guidance for the shared automation tree.
- Shared `.gitignore` policy now protects generated package artifacts while
  preserving tracked repository-owned artifact placeholders.
- Root `tox.ini` now provides a standard entrypoint for repository test, lint,
  quality, security, docs, build, SBOM, and API checks.

### Fixed

- Release-facing package metadata now exposes changelog and security links for
  the runtime and maintainer distributions.
- Package README pages now point readers to PyPI, documentation, source,
  changelog, security policy, and release workflow surfaces.
- Tox checks now delegate installation ownership to the repository make system,
  matching the release-gate execution model.
- API freeze and OpenAPI drift commands now resolve the active Python
  interpreter at execution time.
- Workbook parsing now keeps `defusedxml` as the runtime XML implementation
  while preserving static typing clarity.
- Repository contract tests now follow the enforced Ruff formatting baseline.

## Changelog Scope

Use this file for changes such as:

- root governance and contributor policy
- shared automation under `makes/`
- shared configuration under `configs/`
- root handbook and repository navigation
- repository-level CI, publish, and release process changes
- shared API artifact conventions under `apis/`

Do not use this file for changes that only affect one package release stream
unless the repository-level workflow changed too.
