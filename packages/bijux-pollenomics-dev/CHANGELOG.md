# Changelog

All notable changes for `bijux-pollenomics-dev` are recorded here.

## 0.1.6 - 2026-04-20

### Changed

- Prepared the `v0.1.6` maintainer-tools release line in lockstep with the
  runtime packages so release readiness metadata stays synchronized.

## 0.1.5 - 2026-04-20

### Changed

- Prepared the `v0.1.5` release line by aligning fallback versions and package dependency floors across the repository.
- Synchronized release automation and governance with the `bijux-std v0.1.3` shared standards baseline.

### Fixed

- `release-pypi.yml` now uses parse-safe publication gating for token/bootstrap checks.
- Protected workflow policy checks now accept shared-manifest-driven standards updates through approved control paths.

## 0.1.4 - 2026-04-19

### Changed

- Documentation and release contract checks now target the prefixed handbook
  namespace and canonical docs routes used by the current MkDocs navigation.
- Release workflow contract checks now assert the split publication topology
  (`release-artifacts.yml`, `release-pypi.yml`, `release-ghcr.yml`,
  `release-github.yml`) and remove legacy publish-workflow assumptions.
- Badge synchronization coverage now enforces canonical docs URL expectations
  across repository and package README managed badge blocks.

### Fixed

- Build pipeline verification now enforces stale dist cleanup before package
  builds, preventing mixed-version artifact directories during install smoke
  checks.

## 0.1.3 - 2026-04-16

### Changed

- Maintainer release flow now includes synchronized publishing checks for both
  `bijux-pollenomics` and the `pollenomics` compatibility distribution.
- Source-checkout version fallback now aligns with `0.1.3` for local maintainer
  verification and release readiness checks.

### Fixed

- Repository package-map badge synchronization now includes compatibility
  package surfaces so release status links stay aligned across distributions.
- Dev dependency constraints now require `pytest>=9.0.3` to satisfy security
  gating during release checks.
- Package build metadata now resolves `LICENSE` and `NOTICE` from package-local
  files so isolated sdist installation works during release smoke checks.
- Release tooling now includes a license-asset synchronizer that keeps package
  `LICENSE` and `NOTICE` files aligned with root repository sources.

## 0.1.2 - 2026-04-11

### Changed

- Release history now records the synchronized `v0.1.2` pollenomics
  publication line used by the shared tag-driven release workflow.
- Source-checkout version fallback now aligns with `0.1.2` for maintainer
  release checks and local verification.

## 0.1.1 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.1.1` pollenomics
  publication line used by the shared tag-driven release workflow.
- Source-checkout version fallback now aligns with `0.1.1` for maintainer
  release checks and local verification.

## 0.1.0 - 2026-04-10

### Added

- Repository-owned maintainer package for API freeze checks, OpenAPI drift
  review, quality gates, release support, and documentation integrity checks.
- Package README, changelog, and metadata links for maintainers reviewing the
  first public release.

### Fixed

- API freeze and OpenAPI drift command wiring now resolves the active Python
  interpreter at execution time.
- Repository contract tests now follow the enforced Ruff formatting baseline.
