# Runtime Package Boundaries

`bijux_pollenomics` owns the checked-in sample database and the publication
surfaces derived from it. The package is organized around durable evidence
responsibilities instead of temporary delivery steps.

## Project Intake

Project intake decides which archive accessions enter the repository, which
paper DOI anchors each project, and which source-library bundles must exist
before deeper extraction begins.

Primary modules:

- `bijux_pollenomics.adna.source_library`
- `bijux_pollenomics.adna.ena`

## Paper Capture

Paper capture preserves the citation layer that explains why a project, site,
or chronology claim exists in the first place.

Primary modules:

- `bijux_pollenomics.adna.source_library`
- `bijux_pollenomics.evidence`

## Supplement Capture

Supplement capture archives the project-owned tables, PDFs, and member files
that are later mined into sample-owned rows.

Primary modules:

- `bijux_pollenomics.adna.source_library`
- `bijux_pollenomics.adna.pdf`

## Sample Extraction

Sample extraction converts archive-native and supplement-native identifiers into
stable repository sample rows with explicit lineage back to the project and
paper surfaces.

Primary modules:

- `bijux_pollenomics.adna.sample_master`
- `bijux_pollenomics.adna.sample_truth`

## Site Extraction

Site extraction decides whether a sample owns a named locality, remains
project-level only, or must stay unresolved and blocked from exact geography.

Primary modules:

- `bijux_pollenomics.adna.project_sample_sites`
- `bijux_pollenomics.adna.catalogs`

## Chronology Normalization

Chronology normalization keeps sample-owned dating claims visible, classifies
their strength, and blocks unresolved or conflicting rows from publication.

Primary modules:

- `bijux_pollenomics.adna.project_sample_chronology`
- `bijux_pollenomics.adna.normalization`

## Coordinate Provenance

Coordinate provenance records whether a published point came from direct
coordinates, geocoding, broader projection logic, or a decision not to map the
row.

Primary modules:

- `bijux_pollenomics.adna.coordinate_provenance`
- `bijux_pollenomics.adna.catalogs`

## Output Publishing

Output publishing turns the checked-in sample database into country bundles,
atlas evidence tables, review packets, and release gates without erasing the
underlying evidence posture.

Primary modules:

- `bijux_pollenomics.reporting`
- `bijux_pollenomics.foundation`
