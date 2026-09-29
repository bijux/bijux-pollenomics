# Abborrtjärnen cross-source core lead

The [source-bound comparison](report.json) joins one Neotoma/EPD dataset and
sample to the published LandClim II site metadata as an identity **lead**.
Both sources name Abborrtjärnen and report 107 samples; their site points
differ by 0.334 m. The Neotoma core handle is `ABBO`, while the published
sequence is `ABB`. Their reported elevations differ by 13 m. These facts do
not establish that the same physical core, basin extent or chronology was used.

The selected Neotoma sample 173174 has 23 pollen NISP observations totaling
1,206, including four `Indeterminable` grains, plus six nonpollen observations
totaling 57. Its one retained candidate age is 19 calibrated BP without source
bounds. LandClim metadata row 968 reports a 98 m site radius, `Authors
chronology`, and 3/9799 TopBP/BottomBP labels; the Neotoma dataset reports
−52/9815 calibrated-BP endpoints. No radius, chronology or count denominator
is transferred. The [generated interpretation](REPORT.md) retains the full
bounded comparison, and the [manifest](manifest.json) binds the producer and
inputs.

The producer now reads the governed Neotoma prerequisite projection, its
pinned raw source manifest and a [selected count-mass cross-check](count-mass-crosscheck.json)
extracted from the earlier independent mass audit. Its scientific fields
reproduce the historical working report exactly; only input hashes changed
when disposable process inputs were replaced. Reproduce from the repository
root into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.abborrtjarne_core \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json \
  --raw-manifest data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json \
  --workbook data/landclim/raw/landclim_ii_site_metadata.xlsx \
  --workbook-receipt data/landclim/raw/landclim_sources.json \
  --count-mass docs/report/source-relations/neotoma/abbo-core-identity/count-mass-crosscheck.json \
  --projection docs/report/source-relations/neotoma/lra-prerequisites/projection.json \
  --output artifacts/abbo-core-identity/replay
```

The separate [Rootsi workbook count comparison](../abbo-native-correspondence/README.md)
preserves wider 107-sample taxon and age disagreements. Neither comparison
admits an LRA sample or resolves analytical-use rights.
