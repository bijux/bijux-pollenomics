# Bussjösjön Rootsi and Neotoma source correspondence

The private `rootsi/BUS.xls` workbook and Neotoma/EPD dataset `53995` share
all **69 numeric sample-depth labels**. Across **58 unique casefold-matched
taxon labels**, **1,195/1,195 explicit NISP count cells** agree, representing
44,079 count units. Another **2,807** workbook zero cells have no Neotoma
observation row and remain missing-source cases. This orthographic source
comparison does not define a pollen-only or LRA count denominator.

The workbook repeats both `BETULA` and `PINUS` as column headers. The primary
join excludes all four columns because the header-to-taxon assignment is
ambiguous. A separate **unapplied** diagnostic finds that one column for
each label is zero throughout, while the other matches the corresponding
Neotoma count in all 69 samples. Those **138/138** cells carry **9,076**
additional source count units. The candidate does not alter the primary
44,079-count result or approve a taxon transformation. The
[governed report](report.json) records both results, source hashes and
duplicate-column positions without publishing the private cell-level table.

The workbook has **no sample-age column**. Neotoma's calibrated sample ages
belong to its own `LANDCLIM` chronology; the workbook cannot authenticate
that chronology by itself. The separate
[basin review](../bussjosjon-basin/README.md) retains the 2.5264 km
Neotoma-versus-published-inventory coordinate difference, variable reported
areas, and missing link between the `BUS` core and historical basin geometry.
The author-taxonomy review also preserves excluded and unmapped native
counts. **No Bussjösjön LRA sample is admitted.**

The workbook source is retained externally as
`landclim/rootsi-workbooks/rootsi/BUS.xls`, SHA-256
`f807c5dc0b624db382ce81959ea7d48c348b637018faa873b7ab9ad1f23e197e`.
The [source-custody review](../../rootsi-landclim-overlap/README.md)
records the manifest and unapproved historical-input identity and analytical
reuse rights.

Reproduce from the repository root into an absent local output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.bussjosjon_native_counts \
  --workbook ../bijux-pollenomics-data/landclim/rootsi-workbooks/rootsi/BUS.xls \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json \
  --output artifacts/jobs/bus-native-correspondence-replay
```

Compare its `report.json` with the governed report here. Keep the cell-level
CSV in the local run area while workbook rights remain unresolved.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** BUS and Neotoma share 69 depths and 1,195 exact NISP cells under unique casefold-matched labels.

**Unsupported claim.** Casefold equality and zero-only duplicate candidates do not approve taxon mappings or make missing-source rows observed zeros.

**Actual verification performed.** Read the native correspondence and both unapplied BETULA/PINUS duplicate-column candidates; no private cell rescan.

**Remaining input or review.** Core/coordinate identity, source counting semantics, selected ages, basin support and analytical rights need qualification.

**Cause category.** Duplicate native headers and absent workbook chronology.

**Consequence.** The candidate 9,076 additional counts remain outside the primary 44,079-count comparison.

**Precise next acceptance route.** Obtain source-backed duplicate-column and sample-age decisions and reconcile the 2.5264 km basin conflict before forming an LRA request.

**Negative or refused result.** All four repeated BETULA/PINUS columns are excluded from the primary join; 2,807 missing-source workbook zeros remain; no age column.

**Matched denominator.** 69 depths; 58 unique matched labels; 1,195 primary pairs/44,079 count units; unapplied 138 duplicate-candidate pairs/9,076 count units; 0 admitted samples.

Qualified authored reader SHA-256: `885f67f4815d664b14e338a8b66983bff53cdf480d75b5e32ef2e07d4ff65171`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/bus-native-correspondence/report.json](report.json) (SHA-256 `2c17e6ae80fcdfeb24219193eb9a37ef843ce408d39d3af49f65bc52d2c3d6a8`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
