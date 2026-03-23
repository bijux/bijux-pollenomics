# bijux-pollen

Geographic reporting and data-preparation tools for Nordic aDNA, pollen, environmental archaeology, and archaeology context layers.

## Local Workflow

```bash
make install
make lint
make test
make data-prep
make build
```

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

Detailed source logic and acquisition commands are documented in [`docs/data/README.md`](docs/data/README.md).

## Reports

The generated report and map workflow is documented in [`docs/report/README.md`](docs/report/README.md).
