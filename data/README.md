# Data Layout

Tracked source data lives directly under `data/`:

```text
data
├── aadr
│   └── v66
├── boundaries
├── landclim
├── neotoma
├── raa
└── sead
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- [`docs/data-sources/index.md`](../docs/data-sources/index.md)
- [`docs/reference/data-layout.md`](../docs/reference/data-layout.md)

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.
