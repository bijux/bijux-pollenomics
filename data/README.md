# Data Layout

Tracked source data and governed species-owned ancient-DNA views live directly
under `data/`:

```text
data
├── adna
│   ├── equus_caballus
│   ├── sus_scrofa_domesticus
│   ├── ovis_aries
│   ├── capra_hircus
│   ├── felis_catus
│   ├── equus_asinus
│   ├── gallus_gallus_domesticus
│   ├── meleagris_gallopavo
│   ├── oryctolagus_cuniculus
│   ├── anas_platyrhynchos_domesticus
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
`adna/capra_hircus/`, `adna/felis_catus/`, `adna/equus_asinus/`,
`adna/gallus_gallus_domesticus/`, `adna/meleagris_gallopavo/`,
`adna/oryctolagus_cuniculus/`, and `adna/anas_platyrhynchos_domesticus/`.
