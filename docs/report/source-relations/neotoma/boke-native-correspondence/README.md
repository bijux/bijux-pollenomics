# Bökesjön workbook and Neotoma source correspondence

The separately retained private `rootsi/BOKE.xls` workbook and the governed
[Neotoma/EPD dataset 54001](../../../../../data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json)
have **52/52 identical numeric sample depths**, including fractional labels.
Their depth-matched age numbers differ by at most **0.048410**; all 52 are
within **0.05** of the Neotoma sample-owned calibrated-BP ages. This is
strong numeric evidence for the same selected age vector at the same depths.
The workbook header says `Sample age (LANDCLIM)` without a unit, while the
Neotoma chronology says calibrated radiocarbon years BP and uses a smoothing
spline. Neither source supplies older/younger bounds for the 52 interpolated
sample ages. Numeric correspondence does not independently establish the
workbook's age unit, historical input identity, or uncertainty model.

Among **55 exact shared labels**, **902 of 904 explicit NISP cells** agree.
The two discrepancies are `Pediastrum` at depths 360 and 385: workbook values
3 and 5 versus explicit Neotoma values 2 and 1. There are **1,951** workbook
zero cells and **3** workbook positive cells without a Neotoma observation
row; these are missing-source cases, not Neotoma zero counts. Another two
cells have repeated Neotoma taxon names with different source elements and
remain ambiguous. The workbook has 166 taxon labels, Neotoma has 142, and
only 55 exact strings are shared. The [governed report](report.json) retains
the status totals and unmatched names without publishing the private workbook
or the cell-level comparison table.

The workbook is retained under `landclim/rootsi-workbooks/rootsi/BOKE.xls`
in the external source data store, with SHA-256
`d95da5626a877b340e365317769fa0ef39cf371687b84004a996c30353dc4bc4`.
The [source-custody review](../../rootsi-landclim-overlap/README.md) records
the external manifest. Historical author-input identity and analytical reuse
rights are unapproved. The separate [Bökesjön basin review](../boke-basin/README.md)
does not bind an age-specific radius or lake outline to this core. **No
Bökesjön LRA sample is admitted.** The Neotoma-only observed-pollen study
remains a separate, declared analysis.

Reproduce the source check from the repository root into an absent output
directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.bokesjon_native_counts \
  --workbook ../bijux-pollenomics-data/landclim/rootsi-workbooks/rootsi/BOKE.xls \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json \
  --output artifacts/jobs/bokesjon-native-correspondence-replay
```

The generated `report.json` should match the governed report here. Keep the
cell-level CSV in the local run area while source rights remain unresolved.
