# Data Acquisition Guide

This project stores every tracked source dataset directly under `data/` as one first-class category:

```text
data
├── aadr
│   └── v62.0
├── boundaries
├── neotoma
├── raa
└── sead
```

## Why This Layout

- `aadr/` holds the ancient DNA source metadata that drives the country reports and the shared Nordic map.
- `boundaries/` holds the Nordic country polygons used to classify records by country and to draw map framing layers.
- `neotoma/` holds pollen and paleoecology site data.
- `raa/` holds Swedish archaeology source data from RAÄ / Fornsök.
- `sead/` holds environmental archaeology site data from SEAD.

Each source keeps the same internal contract:

- `raw/` stores a reproducible source snapshot or machine-readable upstream payload.
- `normalized/` stores compact CSV and GeoJSON outputs used directly by the reporting and map pipeline.

We keep these categories separate because they have different licenses, update cadences, spatial semantics, and downstream uses. Keeping them as peer directories makes the tree easier to understand two years later and keeps command lines stable.

The downloader implementation mirrors this layout in [`src/bijux_pollen/data_downloader/`](/Users/bijan/bijux/bijux-pollen/src/bijux_pollen/data_downloader), with one module per tracked data category plus shared helpers for geometry, fetch logic, and normalized record models.

## Why We Track Data In Git

- The generated reports and maps depend on exact source snapshots.
- Review is easier when raw acquisition changes, normalized data changes, and published report outputs are visible in commits.
- The tracked files in this repository are intentionally limited to the inputs we need for reporting and mapping, not the full large genotype matrices.

## AADR

### Why Only `.anno`

For the current reporting workflow we only need the AADR metadata tables with locality, country, latitude, longitude, publication, and date fields. Those fields live in the public `.anno` files.

We do **not** track `.geno`, `.ind`, `.snp`, or spreadsheet companions in this repository because:

- they are much larger than what this map/report workflow needs
- the current pipeline does not read them
- tracking only the `.anno` files keeps the repository focused on geographic reporting inputs

### Source

- Reich Lab datasets page: `https://reich.hms.harvard.edu/datasets`
- Current public AADR release in Harvard Dataverse: `doi:10.7910/DVN/FFIDCW`

### Command

Run:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data aadr --version v62.0 --output-root data
```

This command:

- queries the Harvard Dataverse manifest for the current AADR release
- finds the public `.anno` files for the requested version
- downloads them into tracked locations:
  - `data/aadr/v62.0/1240k/v62.0_1240k_public.anno`
  - `data/aadr/v62.0/ho/v62.0_HO_public.anno`

The command resolves file IDs from Dataverse metadata instead of hardcoding expiring storage URLs.

## Nordic Boundaries, Neotoma, SEAD, and RAÄ

### Why These Sources

- `boundaries/` gives us country membership for every point-based source and a clear country overlay on the shared map.
- `neotoma/` gives us pollen and paleoecology site coverage.
- `sead/` gives us environmental archaeology context and additional site-level pollen relevance.
- `raa/` gives us Swedish archaeology coverage from RAÄ / Fornsök, which is critical for later spatial intersection analysis in Sweden.

### Commands

Run one source at a time with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data boundaries --output-root data
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data neotoma --output-root data
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data sead --output-root data
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data raa --output-root data
```

These commands write:

- `data/boundaries/raw/`: one raw country GeoJSON file per Nordic country
- `data/boundaries/normalized/`: the combined Nordic boundary GeoJSON used by classification and map framing
- `data/neotoma/raw/`: raw Neotoma API snapshot
- `data/neotoma/normalized/`: Nordic pollen CSV and GeoJSON
- `data/sead/raw/`: raw SEAD site snapshot
- `data/sead/normalized/`: Nordic environmental archaeology CSV and GeoJSON
- `data/raa/raw/`: RAÄ capabilities, schema, and Fornsök domain metadata
- `data/raa/normalized/`: Swedish archaeology metadata plus the density GeoJSON used on the map

## Why RAÄ Is Stored As Density For The Map

RAÄ contains hundreds of thousands of published Swedish archaeology records. Rendering every record as a browser marker would make the map heavy and visually noisy. For the current map we therefore store:

- source metadata with total counts
- a normalized Swedish density grid that keeps archaeology visible and fast at national scale

This is a deliberate map-serving decision, not a loss of provenance. The raw RAÄ metadata snapshot is still tracked beside the normalized map layer.

## Refresh Workflow

From the repository root:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
PYTHONPATH=src python3 -m bijux_pollen.cli report-multi-country-map Sweden Norway Finland Denmark --version v62.0 --name nordic --title "Nordic Countries" --context-root data
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Norway --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Finland --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Denmark --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Design Logic

The data model is organized around how the project will answer spatial questions later:

- AADR gives ancient DNA point evidence.
- Neotoma and SEAD give pollen and environmental context.
- RAÄ gives archaeology context in Sweden.
- Boundaries let us apply one consistent country filter across all compatible layers.

That shared country-aware structure is what makes the current map work and what will support later lake buffers, archaeology intersections, and candidate site ranking without another filesystem redesign.

## Unified Collection Logic

`collect-data` treats every tracked source the same way:

- `collect-data aadr` writes `data/aadr/...`
- `collect-data boundaries` writes `data/boundaries/...`
- `collect-data neotoma` writes `data/neotoma/...`
- `collect-data sead` writes `data/sead/...`
- `collect-data raa` writes `data/raa/...`
- `collect-data all` rebuilds the full tracked `data/` tree in one command

This keeps the command model aligned with the filesystem model and makes full rebuilds reproducible after deleting `data/`.
