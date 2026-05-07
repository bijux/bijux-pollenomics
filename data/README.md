# Data Layout

Tracked source data and governed species-owned ancient-DNA views live directly
under `data/`:

```text
data
├── adna
│   ├── species
│   │   ├── equus_caballus
│   │   ├── sus_scrofa_domesticus
│   │   ├── ovis_aries
│   │   ├── bos_taurus
│   │   ├── capra_hircus
│   │   ├── canis_lupus_familiaris
│   │   ├── felis_catus
│   │   ├── camelus_dromedarius
│   │   ├── rangifer_tarandus
│   │   ├── equus_asinus
│   │   └── homo_sapiens
│   │       ├── raw
│   │       │   └── aadr -> ../../../../aadr
│   │       ├── normalized
│   │       ├── manifests
│   │       ├── reports
│   │       └── review
│   ├── governance
│   │   └── source_library
│   └── final
├── aadr
│   └── v66
├── boundaries
├── landclim
├── neotoma
├── raa
└── sead
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- [`docs/02-bijux-pollenomics-data/sources/index.md`](../docs/02-bijux-pollenomics-data/sources/index.md)
- [`docs/02-bijux-pollenomics-data/foundation/directory-layout.md`](../docs/02-bijux-pollenomics-data/foundation/directory-layout.md)

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.

`Homo sapiens` ancient DNA is governed under `adna/species/homo_sapiens/`, while the
domesticated-animal curation program owns species roots such as
`adna/species/equus_caballus/`, `adna/species/sus_scrofa_domesticus/`,
`adna/species/ovis_aries/`, `adna/species/bos_taurus/`,
`adna/species/capra_hircus/`, `adna/species/canis_lupus_familiaris/`,
`adna/species/felis_catus/`, `adna/species/camelus_dromedarius/`,
`adna/species/rangifer_tarandus/`, and `adna/species/equus_asinus/`.

Cross-species audits, caveat ledgers, sample-foundation contracts, and source
registries live under `adna/governance/`, including
`adna/governance/cross_species_bibliography.json`,
`adna/governance/source_library/project_registry.json`, and
`adna/governance/animal_sample_foundation_truth.json`.
Shared atlas-ready and country-ready downstream data products live under
`adna/final/`.
