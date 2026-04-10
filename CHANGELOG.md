# Changelog

This file records notable repository-level changes for `bijux-pollenomics`.

It does not replace package-level release history. Versioning and package-local
release notes belong to each distribution under `packages/`.

Use this changelog for workspace changes that affect multiple packages or
change contributor and maintainer workflows across the repository.

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
