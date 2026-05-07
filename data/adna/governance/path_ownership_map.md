# Animal aDNA Path Ownership Map

This file maps the current owned path families for the animal aDNA foundation.

## Current Layout

- `data/adna/species/<latin_name>/`
  - species-owned sample, site, coordinate, manifest, report, and review files
- `data/adna/governance/`
  - cross-species audits, source registries, caveat ledgers, and publication
    contracts
- `data/adna/final/`
  - shared atlas-ready and country-ready downstream animal outputs

## Path Family Mapping

| Evidence family | Owned path |
| --- | --- |
| species sample, site, and coordinate files | `data/adna/species/<latin_name>/...` |
| project and paper source library | `data/adna/governance/source_library/...` |
| cross-species sample and map-readiness contracts | `data/adna/governance/...` |
| shared atlas candidate products | `data/adna/final/atlas/...` |
| shared country publication products | `data/adna/final/countries/...` |

## Why This Split Exists

- species roots keep the evidence chain readable per taxon
- governance files stop cross-species audits from polluting the root
- final outputs stop shared downstream products from being confused with source
  evidence
