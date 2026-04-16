# Changelog

All notable changes for `pollenomics` are recorded here.

## 0.1.3 - 2026-04-16

### Added

- First public compatibility release for the `pollenomics` alias distribution.
- CLI entry point `pollenomics` now dispatches to the same runtime behavior as
  `bijux-pollenomics`.
- Public Python API is now available under the `pollenomics` module as a
  compatibility re-export of `bijux_pollenomics`.

### Changed

- Package README now follows the shared badge map used across Bijux packages,
  including source, docs, release, and distribution status links.
- Development dependency constraints now require `pytest>=9.0.3` so security
  verification passes with current pip-audit advisories.

### Fixed

- Package build metadata now resolves `LICENSE` and `NOTICE` from package-local
  files so isolated sdist installation works during release smoke checks.
