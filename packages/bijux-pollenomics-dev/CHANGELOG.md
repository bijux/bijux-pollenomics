# Changelog

All notable changes for `bijux-pollenomics-dev` are recorded here.

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
