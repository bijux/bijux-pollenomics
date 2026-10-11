# EMPD2–NFI observed vegetation pairing decision

The [pair ledger](pairs.csv) records **16 geographic proximity leads and zero admitted observed vegetation pairs**. The [machine-readable report](report.json) binds each refusal to the original EMPD2 SQLite and Swedish NFI workbook SHA-256 identities. This is an outcome-free source review: NFI tree measurement cells were not read, no vegetation reconstruction was evaluated, and no benchmark threshold was frozen.

## Source and denominator

The original Swedish subset has 132 EMPD2 metadata samples. The NFI workbook has 43,892 plot-year rows across 6,018 distinct tract/plot keys. WGS84 inverse-geodesic screening after transforming NFI points from SWEREF99 TM gives 53 plot-year/sample combinations within 1 km, across 16 pollen samples. The ledger selects one nearest NFI plot-year per sample, including 14 distinct selected plot-years. Distance is only a lead-generation screen. It does not establish shared time, vegetation footprint, measurement units, or independent validation support.

The original source dossier and spatial screen remain in the local ignored archive because they contain exact NFI row locations. Their paths and SHA-256 values are in `report.json`; they are optional inputs for local source-bound replay. The tracked [SLU calibration guide](inputs/slu-calibration-guide.pdf) is an exact byte copy of its original. The EMPD2 SQLite and NFI workbook also remain outside the tracked report. The producer checks their exact hashes and reads only the NFI workbook's first six identity/coordinate fields to bind every selected plot-year to an original row and recompute each geodesic distance. The source-native NFI date is preserved only in the ignored local `pairs-source-bound.csv`; pollen `agebp` is not treated as a collection year. The tracked CSV replaces each NFI row location and key with an opaque SHA-256 identity; it contains no NFI tract, plot, year, date, or coordinates.

[PANGAEA's EMPD2 source record](https://doi.org/10.1594/PANGAEA.909130) identifies the pollen source and CC BY 4.0 terms. The [SLU National Forest Inventory calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf) states CC0 1.0 terms and describes temporary forest plot observations intended for calibration or validation of remote-sensing products. Plot observations cannot by themselves establish regional vegetation area totals or means.

## Current decision

All 16 leads lack an authenticated pollen collection date, an opened and unit-checked NFI tree measurement target, an effective plot-area denominator, a pollen taxon denominator and tree-taxon crosswalk, and a reviewed rule mapping a plot observation to the pollen basin or reconstruction support. Five leads also have unresolved cross-source physical sample identity; one collection note requires authentication. The benchmark still lacks a qualified independent-source/leakage review and non-null predeclared minimum sample and error thresholds. Each missing field is explicit in the CSV. The 16 rows are **refusals for the current benchmark**, not 16 negative measured observations.

The bounded decision can be replayed with the original raw holdings and tracked review inputs:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.empd2_nfi_pairing \
  --repository . \
  --empd2-source artifacts/v3/reference/empd2-intake001/EMPD2.sqlite3 \
  --nfi-workbook artifacts/v3/reference/swedish-nfi-plot001/swe_nfi_plotdata2.xlsx \
  --output artifacts/jobs/empd2-nfi-pairing/publication
```

The output destination must be absent. Source-bound replay requires the raw files and original review reports at the paths above; default focused tests exercise the tracked guide, public output and refusal contract without them. The generated public CSV and JSON in this directory are byte-identical to the source-bound replay's public projection. The ignored local replay also retains the exact source-row ledger for private verification. The decision can change only after the missing source facts and scientific review are supplied, then with a new source-bound record; proximity alone cannot promote a lead.
