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
