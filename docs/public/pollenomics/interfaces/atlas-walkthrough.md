---
title: Walk Through One Atlas Result
audience: reader
type: how-to
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-02
---

# Walk Through One Atlas Result

Start with the [product guide](../index.md), then open the [Nordic Evidence
Atlas](../../nordic-atlas/index.md). The current product is an `atlas_builder`:
it collects and normalizes source evidence, publishes atlas and country
bundles, and offers bounded exploratory methods. It is not a scientific
decision engine or an accepted vegetation-accuracy result. This walkthrough
follows one published LandClim II **modeled-context** row from the atlas to its
source-bound summary and reproduces that summary without changing the
published files.

Three identities matter. The **runtime** is the installed command and its
version. The **evidence revision** is the checkout and the input hashes in the
result receipt. The **publication product** is the selected Nordic atlas and
its governed files. A working command establishes runtime behavior; it does
not by itself establish that a source is complete or a result scientifically
validated.

## Install and inspect the scope

Use a source checkout with Python 3.11 or later and `uv`. From its root,
follow the [locked setup instructions](../operations/installation-and-setup.md)
and run:

```bash
make install
artifacts/root/check-venv/bin/bijux-pollenomics --version
git rev-parse HEAD
git status --short
artifacts/root/check-venv/bin/bijux-pollenomics product-scope --json
artifacts/root/check-venv/bin/bijux-pollenomics source-support --json
artifacts/root/check-venv/bin/bijux-pollenomics validate-collection-summary \
  --summary-path data/collection_summary.json
```

The inspection commands do not collect sources or publish a map. In the
checked checkout, `product-scope` reports `atlas_builder` and lists
scientifically accepted LRA and independent vegetation accuracy among
unsupported claims.
`source-support` reports implemented adapters for seven source families;
`validate-collection-summary` confirms the existing seven-source summary's
structure. “Implemented” and “validated summary” do not mean that every
source record is admitted, current, or fit for a particular scientific claim.
The [operator workflows](operator-workflows.md) explain which later commands
write data or publications.

## Find the atlas layer and its source row

From the [Nordic atlas page](../../nordic-atlas/index.md), open the
[interactive map](../../../report/regions/nordic/nordic_map.html). Open
**Show controls** if the filter panel is closed, then expand **Modeled context**.
The controls panel scrolls independently on a small screen. Choose **Show modeled metric** to activate the layer. Select the
source land-cover type family, **Open land**, and the published **0–100 BP**
window. Changing the window updates the active layer; the toggle then reads
**Hide modeled metric**. “BP” is
the source's years-before-present window label, not a newly dated pollen
sample. The map displays individual grid cells from a published REVEALS
vegetation reconstruction. Its visible-frame download retains the selected
cell values and source window. Do not read a cell as an observed vegetation
measurement or a continuous interpolation between windows.

For one cell, the normalized source grid
`data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson` has
`record_id=937075:1030:0-100-bp`. Its popup identifies Sweden, grid cell
`1030`, the source DOI, and the `0-100 BP` window. Read that exact record from
the checkout:

```bash
artifacts/root/check-venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path('data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson')
features = json.loads(path.read_text(encoding='utf-8'))['features']
cell = next(feature['properties'] for feature in features
            if feature['properties']['record_id'] == '937075:1030:0-100-bp')
print(cell['record_id'], cell['country'], cell['time_label'])
print(cell['reconstruction_values']['OL'], cell['standard_errors']['OL'])
PY
```

It reads `29.0510048529897` percent modeled open-land cover with source
standard error `8.98674192646519` percentage points. Its provenance points
to `LANDCLIMII.RV.means.JUN2021/TW1.RV.estimates.jun21.csv` inside the
retained LandClim II archive. That is a model result for one grid cell, not a
country estimate or measured vegetation.

The companion [panel CSV](../../../report/regions/nordic/landclim-modeled-panels/panels.csv)
provides a compact source-to-result check. Find the row with `country=Sweden`,
`source_window=0-100 BP`, and `metric_key=OL`:

| Field | Published companion-row value | Interpretation |
| --- | ---: | --- |
| `cell_count` | 26 | source-grid cells assigned to Sweden in this window |
| `modeled_count` | 24 | cells with usable modeled values |
| `high_quality_count` / `low_quality_count` | 11 / 13 | source quality labels among modeled cells |
| `no_pollen_data_count` | 2 | placeholders excluded from numeric ranges |
| `minimum_estimate_percent` / `maximum_estimate_percent` | 15.506724107 / 89.8378153552 | extrema of individual-cell modeled open-land percentages |
| `minimum_standard_error_percent` / `maximum_standard_error_percent` | 2.07094958371 / 19.4680580393 | extrema of individual-cell source standard errors, in percentage points |

These extrema do not describe a country mean. The standard errors are not
pooled or converted to confidence intervals. The [panel explanation and
receipt](../../../report/regions/nordic/landclim-modeled-panels/README.md)
identify the 400 country × window × metric rows (four countries, 25 windows,
four metrics), the 1,875-row input temporal grid, input hashes, quality
counts, and [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075) source.
Open land (`OL`) is a land-cover type; the agricultural-land/cereals (`AL`)
panel is a plant functional type component within it, not another disjoint
land-cover class.

## Reproduce the bounded summary

The installed repository environment includes the development producer. Use
an **absent** output directory under `artifacts/`; this command writes only
that new directory. It reads the checked-in normalized LandClim grid and
parameter table, validates the modeled-context manifest, and emits a CSV and
JSON receipt:

```bash
PYTHONDONTWRITEBYTECODE=1 artifacts/root/check-venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_modeled_panels \
  --repository . --output artifacts/jobs/landclim-panel-review
cmp artifacts/jobs/landclim-panel-review/panels.csv \
  docs/report/regions/nordic/landclim-modeled-panels/panels.csv
cmp artifacts/jobs/landclim-panel-review/report.json \
  docs/report/regions/nordic/landclim-modeled-panels/report.json
```

At the checked-in evidence revision used for this tutorial, both comparisons
matched byte for byte. A different source revision may produce a difference;
inspect the input SHA-256 values and source labels in the two receipts before
interpreting it. The producer creates a descriptive summary of an existing
model output. It does not rerun the historical LandClim reconstruction or
establish an independent vegetation reference.

## Decide what the result supports

The modeled layer is environmental **context**. The atlas also contains
admitted, source-linked direct-evidence features, reference geography, and
other context layers; their roles and units remain distinct in the [Nordic
atlas inventory](../../nordic-atlas/index.md). A source-support adapter, a
map point, and a modeled cell are not interchangeable admissions. Nearby
features are not necessarily linked in time or causal process.

For a vegetation-accuracy claim, a separate measured vegetation target would
need matched site, time, taxon response, and spatial support. The current
[vegetation-reference decision](../science/results.md#measured-vegetation-evidence)
admits zero measured pairs among 16 nearby EMPD2–NFI candidates, so this
walkthrough yields no accuracy score. Exploratory REVEALS/LOVE commands also
require their own complete count, chronology, basin, pollen productivity, and
transport inputs; this atlas row does not supply those inputs. If the source
row or required inputs are missing, retain the missing-input or refusal result
and follow the [source prerequisites](../science/sources.md#before-a-core-can-enter-lra) rather
than filling gaps with invented collections.
