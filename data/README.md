# Data Layout

Tracked source data and governed species-owned ancient-DNA views live directly
under `data/`:

```text
data
├── adna
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

`Homo sapiens` ancient DNA is governed under `adna/homo_sapiens/`, where the
species-owned raw AADR view points back to the versioned source intake while
keeping normalized, manifest, review, and report ownership visible.
