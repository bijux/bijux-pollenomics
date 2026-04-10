# Changelog

All notable changes for `bijux-pollenomics-dev` are recorded here.

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
