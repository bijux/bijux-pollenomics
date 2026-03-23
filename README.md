# bijux-pollen

Geographic reporting and data-preparation tools for Nordic aDNA, pollen, environmental archaeology, and archaeology context layers.

## Local Workflow

```bash
make install
make reports
make app-state
make check
make lint
make test
make data-prep
make docs
make docs-serve
make build
```

## Documentation

The canonical documentation site is built with MkDocs and lives under `docs/`.

- `make docs` builds the static site into `artifacts/docs/site`
- `make docs-serve` serves the site locally on `127.0.0.1:8000`
- `make install` creates the local virtual environment under `artifacts/.venv/`
- `make reports` regenerates the checked-in shared map and country report bundles under `docs/report/`
- `make app-state` rebuilds the current app scope end to end: tracked data, published reports, and the docs site
- `make check` runs lint, tests, and docs as one repository verification pass
- `make build` writes source and wheel distributions into `artifacts/dist/`
- the documentation homepage leads with the shared Nordic map in `docs/report/nordic/nordic_aadr_v62.0_map.html`

## Data Model

Tracked source data lives directly under `data/`:

```text
data
├── aadr
├── boundaries
├── neotoma
├── raa
└── sead
```

Detailed source logic and acquisition commands are documented in the canonical MkDocs data guide:

- [`docs/03-data-guide/index.md`](docs/03-data-guide/index.md)
- [`docs/07-reference/data-layout.md`](docs/07-reference/data-layout.md)

## Reports

The generated report and map workflow is documented in the canonical MkDocs reports section:

- [`docs/04-reports/index.md`](docs/04-reports/index.md)
- [`docs/07-reference/report-layout.md`](docs/07-reference/report-layout.md)

## Current Scope

The current app scope is:

- track five source categories under `data/`
- publish one shared Nordic map under `docs/report/nordic/`
- publish country-level AADR bundles for Sweden, Norway, Finland, and Denmark
- keep the full state rebuildable from checked-in commands and tracked outputs

The current app does not yet score candidate sites, compute lake intersections, or rank sampling locations automatically.
