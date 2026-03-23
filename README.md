# bijux-pollen

Geographic reporting and data-preparation tools for Nordic aDNA, pollen, environmental archaeology, and archaeology context layers.

## Local Workflow

```bash
make install
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
