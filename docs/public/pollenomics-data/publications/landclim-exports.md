---
title: LandClim Exports
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# LandClim Exports

LandClim exports provide Nordic pollen-sequence locations and REVEALS
vegetation-reconstruction coverage. They are environmental context with their
own observation units and time windows, not background decoration for an aDNA
map.

## Current Governed Surface

The checked-in normalized state contains:

| Surface | Count | Observation unit |
| --- | ---: | --- |
| pollen site-sequence rows | 492 | dataset-specific site sequence |
| rows with supported numeric time bounds | 482 | site sequence with numeric BP posture |
| REVEALS grid cells | 88 | reconstructed vegetation coverage cell |

The normalized artifacts are:

- `nordic_pollen_site_sequences.csv` for tabular reuse;
- `nordic_pollen_site_sequences.geojson` for site locations;
- `nordic_reveals_grid_cells.geojson` for reconstruction coverage; and
- `landclim_summary.json` for layer identities and counts.

```mermaid
flowchart LR
    Datasets["PANGAEA LandClim datasets"] --> Sites["492 site-sequence rows"]
    Datasets --> Grids["88 REVEALS grid cells"]
    Sites --> Time["482 rows with numeric BP bounds"]
    Sites --> Context["pollen-site context layer"]
    Grids --> Context
    Time --> Compare["qualified temporal comparison"]
```

## Site Rows And Grid Cells Are Not Interchangeable

A site row identifies one dataset-specific pollen sequence at a location and
can carry its own time window, source URL, and sequence metadata. A grid cell
summarizes published REVEALS coverage and can combine variables, datasets, and
multiple time windows. One site can contribute to broader reconstruction
context; that relationship does not make the site and cell the same record.

Names can recur across LandClim datasets. Stable `record_id` values retain the
dataset and location identity needed to avoid merging similarly named site
sequences by display label alone.

## Temporal Reading

Numeric `time_start_bp` and `time_end_bp` values support interval-aware
filtering for the 482 qualified rows. They do not guarantee equal dating
resolution, identical sampling intervals, or event-level contemporaneity with
an aDNA sample. The remaining rows are not zero-dated; their numeric posture is
unavailable under the normalized contract.

REVEALS grid cells can span many windows. Use their declared window coverage
rather than collapsing a cell to a single date. A cell's broad reconstruction
span must not be treated as a sample-owned chronology.

## Worked Record: Aal Præstesø

The normalized LandClim feature for **Aal Præstesø** demonstrates the minimum
portable site-sequence claim:

| Field | Governed value | Interpretation |
| --- | --- | --- |
| `record_id` | `897303:Aal Præstesø:55.637778:8.257222` | dataset, label, and reported position form the retained record identity |
| country | Denmark | publication grouping, not the scientific identity |
| geometry | `8.257222, 55.637778` | GeoJSON longitude then latitude |
| source | `https://doi.org/10.1594/PANGAEA.897303` | LandClim dataset lineage |
| interval | `100-350 BP` | coverage attached to this site-sequence row |
| observation unit | one site sequence | not one pollen grain, sample event, or REVEALS cell |

The interval permits interval-aware filtering at the **site-sequence** level.
It does not state that every observation within the sequence has that date or
that another record overlapping `100-350 BP` represents the same event. If the
feature is exported without its `record_id`, source DOI, and observation unit,
the remaining name and point are insufficient to reconstruct that meaning.

```mermaid
flowchart LR
    Dataset["PANGAEA 897303"] --> Sequence["Aal Præstesø site sequence"]
    Sequence --> Place["reported point in Denmark"]
    Sequence --> Window["100-350 BP coverage"]
    Sequence --> Layer["LandClim pollen context"]
    Window -. "not an event date" .-> Layer
```

## Reuse Contract

Keep record identity, source DOI, geometry type, observation unit, dataset,
time bounds and label, record count, and popup/source details with each row.
When aggregating, keep site sequences separate from grid cells and state
whether the denominator is 492 site rows, 482 numerically qualified rows, or
88 coverage cells.

Continue to [LandClim source guidance](../sources/landclim.md) for acquisition
and normalization, [maps](maps.md) for layer interpretation, and
[chronology guidance](../evidence/chronology.md) for cross-family time claims.
