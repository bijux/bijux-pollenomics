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
`fb444e5a079f6e18bfa4d4a225fd5f9dd2d3dab471f6949ab39d73cb6dd24204`;
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
