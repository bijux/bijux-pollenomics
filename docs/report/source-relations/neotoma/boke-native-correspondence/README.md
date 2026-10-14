# Bökesjön workbook and Neotoma source correspondence

The separately retained private `rootsi/BOKE.xls` workbook and the governed
[Neotoma/EPD dataset 54001](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json)
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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** BOKE and Neotoma share 52 numeric depths and 52 age-number comparisons within 0.05, with explicit count agreement/refusal states.

**Unsupported claim.** Numeric age proximity cannot identify workbook units or historical age model; missing source rows are not zeros.

**Actual verification performed.** Read the depth/age/count correspondence JSON, including both discrepant Pediastrum pairs and ambiguous duplicate cases; no workbook replay.

**Remaining input or review.** Selected historical age model, taxon/unit/count semantics, basin geometry and workbook use rights remain unresolved.

**Cause category.** Strong numeric correspondence has incomplete semantic authority.

**Consequence.** Neither a complete matched count matrix nor an executable LRA request is established.

**Precise next acceptance route.** Resolve the two Pediastrum discrepancies and missing/ambiguous source cells with original sample/age/rights authority before admission.

**Negative or refused result.** 902 of 904 explicit pairs agree; 2 differ; 1,951 workbook zeros and 3 positives have no source row; 2 cases remain ambiguous.

**Matched denominator.** 52 depths; 55 exact shared labels of 166 workbook/142 Neotoma labels; 904 explicit NISP comparisons; 0 LRA samples.

Qualified authored reader SHA-256: `4e29365497c3d70bd57f5fd4de4cc549a70049b78c4bd253c38189c23adcdfd6`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/boke-native-correspondence/report.json](report.json) (SHA-256 `4dd04b4c1216cf4118852e18faf212c15c0f5c7a9bafa31afb639eb65a197fc1`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
