# Runtime Package Boundaries

`bijux_pollenomics` owns the checked-in sample database and the publication
surfaces derived from it. The package is organized around durable evidence
responsibilities instead of temporary delivery steps.

## Runtime Command Surface

The command surface turns CLI arguments into one owned runtime action. It is
the only layer that should know how operator intent maps onto collection,
normalization, review, or publication entrypoints.

Primary modules:

- `bijux_pollenomics.command_line.parsing`
- `bijux_pollenomics.command_line.runtime`

## Source Collection And Intake

Source collection and intake admit external source-family data into tracked
repository state. This includes general context sources and the intake helpers
that decode source-owned workbook structure.

Primary modules:

- `bijux_pollenomics.data_downloader.pipeline`
- `bijux_pollenomics.data_downloader.sources`
- `bijux_pollenomics.data_downloader.intake`
- `bijux_pollenomics.data_downloader.exports`
- `bijux_pollenomics.adna.sources.library`
- `bijux_pollenomics.adna.sources.ena`

## Evidence Normalization

Evidence normalization turns admitted source material into species-aware sample,
site, chronology, and coordinate surfaces that the repository can review and
publish honestly.

Primary modules:

- `bijux_pollenomics.adna.projects.sample_master`
- `bijux_pollenomics.adna.projects.sample_truth`
- `bijux_pollenomics.adna.projects.sample_sites`
- `bijux_pollenomics.adna.projects.sample_chronology`
- `bijux_pollenomics.adna.projects.sample_locality_evidence`
- `bijux_pollenomics.adna.projects.coordinate_provenance`
- `bijux_pollenomics.adna.normalization`
- `bijux_pollenomics.adna.catalogs`

## Evidence Review

Evidence review classifies what the repository can claim, what remains blocked,
and which review surfaces or ranking surfaces must exist before publication.

Primary modules:

- `bijux_pollenomics.adna.reviews`
- `bijux_pollenomics.evidence`
- `bijux_pollenomics.analysis.review`
- `bijux_pollenomics.foundation`

## Publication Assembly

Publication assembly turns checked-in evidence into atlas bundles, country
bundles, and scope-filtered output payloads without erasing the upstream
evidence posture.

Primary modules:

- `bijux_pollenomics.reporting.adna`
- `bijux_pollenomics.reporting.bundles`
- `bijux_pollenomics.reporting.context`

## Public Artifact Writing

Public artifact writing formats and writes the governed report tree under
`docs/report/`.

Primary modules:

- `bijux_pollenomics.reporting.presentation`
- `bijux_pollenomics.reporting.rendering`
- `bijux_pollenomics.reporting.map_document`
- `bijux_pollenomics.reporting.review`

## Package Split

The repository keeps three distributions for three audiences:

- `bijux_pollenomics` is the canonical runtime and scientific owner
- `bijux_pollenomics_dev` is maintainer tooling and must not absorb runtime
  scientific logic
- `pollenomics` is a compatibility alias and must not drift into an
  independent runtime

## Cross-Tree Contract

- `data/` holds tracked source, normalized, and reviewed evidence surfaces
- `docs/report/` holds governed public artifacts and review surfaces
- `docs/` explains those surfaces but does not replace them
