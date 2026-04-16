# Changelog

All notable changes for `bijux-pollenomics` are recorded here.

## 0.1.3 - 2026-04-16

### Changed

- Default AADR release now targets `v66`, and command/documentation examples
  now use `v66` as the canonical release input.
- AADR release resolution now supports current Dataverse filename formats
  (including dotted `v66` naming) while keeping stable `1240k` and `ho`
  dataset extraction.
- AADR schema handling now accepts current release header variants so report
  generation works with the latest `.anno` files.
- Shared atlas layer naming now includes the active AADR release label, for
  example `AADR-v66 aDNA samples`.

### Fixed

- Build validation now smoke-tests installation for both wheel and sdist
  artifacts before considering package builds ready.
- Installation guidance now explicitly documents the Python `3.11+` runtime
  requirement and common `Requires-Python` install failure symptom.
- Package build metadata now resolves `LICENSE` and `NOTICE` from package-local
  files so isolated sdist installation works during release smoke checks.
- Build smoke verification now installs package dependencies and starts from a
  clean artifact directory so wheel and sdist checks run against one build set.

## 0.1.2 - 2026-04-11

### Changed

- Release history now records the synchronized `v0.1.2` pollenomics
  publication line used by the shared tag-driven release workflow.
- Source-checkout version fallback now aligns with `0.1.2` so local CLI
  version output stays consistent with package metadata.

## 0.1.1 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.1.1` pollenomics
  publication line used by the shared tag-driven release workflow.
- Source-checkout version fallback now aligns with `0.1.1` so local CLI
  version output stays consistent with package metadata.

## 0.1.0 - 2026-04-10

### Added

- Runtime package for rebuilding checked-in Nordic evidence data, report
  bundles, and atlas artifacts from repository-owned commands.
- Public CLI entry point for data collection, report publishing, and local
  repository verification workflows.
- Package metadata, README links, changelog, and security references for the
  first public release.

### Fixed

- Workbook parsing now keeps `defusedxml` as the runtime XML implementation
  while preserving static typing clarity.
