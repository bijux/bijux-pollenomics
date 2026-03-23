# Data Layout

Tracked source data lives directly under `data/`:

```text
data
├── aadr
│   └── v62.0
├── boundaries
├── neotoma
├── raa
└── sead
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- [`docs/03-data-guide/index.md`](../docs/03-data-guide/index.md)
- [`docs/07-reference/data-layout.md`](../docs/07-reference/data-layout.md)

Transient local tooling outputs such as the virtual environment and package distributions live under `artifacts/`, not under `data/`.
