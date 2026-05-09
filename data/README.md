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

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical public docs pages:

- [`docs/public/pollenomics-data/sources/index.md`](../docs/public/pollenomics-data/sources/index.md)
- [`docs/public/pollenomics-data/overview/data-directory-layout.md`](../docs/public/pollenomics-data/overview/data-directory-layout.md)

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.

The data root also ships contract surfaces that explain ownership instead of
forcing readers to infer it from directory names alone:

- `source_family_contracts.json`
- `source_family_evidence_stage_matrix.json`
- `source_fact_ownership_registry.json`
- `evidence_artifact_contracts.json`

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
The role split inside that tree is made explicit in
`adna/governance/surface_role_registry.json`, and the shared per-project file
contract lives in `adna/governance/source_library/project_surface_contract.json`.
Shared atlas-ready and country-ready downstream data products live under
`adna/final/`.
