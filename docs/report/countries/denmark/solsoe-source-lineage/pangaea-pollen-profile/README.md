# Solsø 1981 primary pollen-count lineage

The primary [EPD/PANGAEA pollen profile](https://doi.org/10.1594/PANGAEA.739834)
is a 66-depth, 147-parameter count table for the `SOLSOE81` 1981 core. Its
source text is retained privately under `landclim/pangaea/solsoe/` with
SHA-256 `da790080493ccfe7e37ab16d154e438cfbeb7b0046bc41d7f24499572a0353d0`.
PANGAEA attributes the data to Bent V. Odgaard and the European Pollen
Database under CC BY-NC 3.0. The raw table is not redistributed here.

The [source-bound comparison](report.json) joins those **66 depths exactly**
to Neotoma collection unit `4303` at site `3432`. Decimal centimetre
conversion is exact; an earlier float-truncation diagnostic had falsely
suggested four 1 cm differences. Across the **9,702** depth × parameter
cells, the primary table has **2,881 positive counts** and **6,821 zeros**.
Neotoma records exactly those **2,881 positive NISP observations**, no more
and no fewer; every matched count is equal. Their total is **128,653**. The
[sample ledger](samples.csv) identifies every depth, Neotoma sample ID,
positive taxon count and row total. Report SHA-256 is
`e71e6ef7fb52afd2abf5540d1a003d4008e9520e58a39980296cba88d1003c2b`;
sample ledger SHA-256 is
`a4f41777c1b4cbe104aaa7fb78355b9d7ad249bb81b4ace401eb07e9cceef010`.

**129** PANGAEA parameter names match Neotoma source-reported names exactly.
The other **18** each have one unique Neotoma name with an identical 66-depth
count vector. The report retains those as numerical source-name candidates,
including their positive-depth counts and totals. Some are modernized names;
count-vector identity alone is not qualified ecological taxonomy approval.
The PANGAEA zero cells correspond to missing rows in Neotoma's sparse
positive-observation export. The 128,653 total spans all 147 primary
parameters and is not silently treated as a terrestrial pollen denominator
or a 31-target LandClim PPE denominator.

The source text and retained Neotoma manifest, sample part and eight
observation parts are SHA-checked by the [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py).
The same primary core's [34 radiocarbon controls](../pangaea-core-controls/README.md)
were compared separately. These joins establish the 1981 core's count and
control lineage; they still do not select the **79** samples in the LandClim II
author sequence, identify its chronology, provide age-specific basin
geometry or admit any Danish LRA sample.

Replay the derived comparison into `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.solsoe_pollen_lineage \
  --repository . --source-root /path/to/bijux-pollenomics-data \
  --output artifacts/jobs/solsoe-pollen-lineage/replay
cmp docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report.json \
  artifacts/jobs/solsoe-pollen-lineage/replay/report.json
cmp docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/samples.csv \
  artifacts/jobs/solsoe-pollen-lineage/replay/samples.csv
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

**Supported claim.** The retained primary 1981 profile comparison matches all 66 depths and 2881 positive count cells exactly to Neotoma sparseNISP observations.

**Unsupported claim.** Identical 66-depth count vectors do not qualify ecological synonymy, terrestrial-only pollen totals,31PPE-target denominators, author 79 sample selection or LRA basins.

**Actual verification performed.** The maintained source-built isolated-standard-library replay and independent native source observer both returned zero on d87e7ff50c7c21c9a3dab5125db2e2cfdd6c4a9b. Complete report and ordered66-row sample ledger match publication byte-for-byte; independent full9702-cell reconciliation found2881 positive and6821 zero cells,128653 total counts,129 literal names and18 unique numerical name-vector candidates. All3510 original input identities and same-process source/runtime observations are retained. No ecological taxonomy approval or original provider acquisition is inferred.

**Remaining input or review.** The 18 numeric rename candidates require qualified taxonomy; historical sample/chronology selection, dated basins and noncommercial source reuse remain separate requirements.

**Cause category.** Primary count/depth correspondence with sparse-zero and taxonomic interpretation limits.

**Consequence.** Sparse absent Neotoma rows correspond to source zeros here; the all 147 parameter total cannot silently become a terrestrial pollen or author-target denominator.

**Precise next acceptance route.** Use the separately retained two-product execution/source-custody capsule for this count-lineage result. Review all18 numerical name candidates under qualified ecological taxonomy, then resolve original79 sample/chronology selection, dated basin and noncommercial reuse requirements before any LRA admission.

**Negative or refused result.** The 18 names remain numeric_source_name_candidate_not_ecological_approval; author 79 selection and chronology are unidentified; LRA-admitted 0.

**Matched denominator.** 66 depths×147 parameters=9702 cells;2881 positive observations+6821 zeros;totalNISP128653;129 same-name parameters+18 numeric rename candidates; zero admitted LRA samples.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/report.json](report.json) (SHA-256 `e71e6ef7fb52afd2abf5540d1a003d4008e9520e58a39980296cba88d1003c2b`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/pangaea-pollen-profile/samples.csv](samples.csv) (SHA-256 `a4f41777c1b4cbe104aaa7fb78355b9d7ad249bb81b4ace401eb07e9cceef010`).

- [Retained qualification evidence: reports/science/source-lineage/solsoe-primary-pollen-source.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/solsoe-primary-pollen-source.json) (SHA-256 `144bcba6b8afe53a63dc7b571ca197047c2d57bbf0cc4535e9d3c0333bf9765c`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
