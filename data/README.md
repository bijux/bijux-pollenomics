# Data Layout

Tracked source data and governed species-owned ancient-DNA views live directly
under `data/`:

```text
data
├── adna
│   ├── equus_caballus
│   ├── sus_scrofa_domesticus
│   ├── ovis_aries
│   ├── bos_taurus
│   ├── capra_hircus
│   ├── canis_lupus_familiaris
│   ├── felis_catus
│   ├── camelus_dromedarius
│   ├── rangifer_tarandus
│   ├── equus_asinus
│   └── homo_sapiens
│       ├── raw
│       │   └── aadr -> ../../../aadr
│       ├── normalized
│       ├── manifests
│       ├── reports
│       └── review
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

`Homo sapiens` ancient DNA is governed under `adna/homo_sapiens/`, while the
domesticated-animal curation program owns species roots such as
`adna/equus_caballus/`, `adna/sus_scrofa_domesticus/`, `adna/ovis_aries/`,
`adna/bos_taurus/`, `adna/capra_hircus/`, `adna/canis_lupus_familiaris/`,
`adna/felis_catus/`, `adna/camelus_dromedarius/`, `adna/rangifer_tarandus/`,
and `adna/equus_asinus/`.

Cross-species animal aDNA audits live directly under `adna/` as checked-in
artifacts such as `cross_species_bibliography.json`,
`cross_species_archive_inventory.csv`, `cross_species_coverage_dashboard.json`,
`cross_species_freshness.csv`, and `shipped_product_audit.json`.
Each tracked non-human species root also keeps `raw/source_snapshot.json` and
`raw/source_snapshot.csv` so archive-facing study wording is preserved alongside
the narrower curated inventory tables.
