# Changelog

All notable changes for `pollenomics` are recorded here.

## 0.1.5 - 2026-04-20

### Changed

- Prepared the `v0.1.5` release line by aligning fallback versions and package dependency floors across the repository.
- Synchronized release automation and governance with the `bijux-std v0.1.3` shared standards baseline.

### Fixed

- `release-pypi.yml` now uses parse-safe publication gating for token/bootstrap checks.
- Protected workflow policy checks now accept shared-manifest-driven standards updates through approved control paths.

## 0.1.4 - 2026-04-19

### Changed

- Compatibility package documentation URL metadata now points to the canonical
  handbook route under `02-bijux-pollenomics-data`.
- Package README managed badge surfaces now align with canonical handbook docs
  paths so compatibility package docs links resolve consistently with runtime
  package links.
- Compatibility package contract tests now assert prefixed handbook paths and
  split release-workflow documentation references.

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
