# Bussjösjön and Bökesjön core leads

The [source-bound comparison](report.json) checks Neotoma/EPD datasets 53995
and 54001 against LandClim II metadata rows 978 and 977. For Bussjösjön and
Bökesjön respectively, both sources list 69 and 52 samples, while their site
points differ by 0.383 m and 0.445 m. The Neotoma and published elevations
differ by 211 m and 33 m. These are review leads, not established common cores
or basin geometries. The published 69 m and 80 m radii are not transferred.

The native sequences contain 68,668 and 42,548 pure-pollen NISP units, plus
15,561 and 10,280 other NISP units. All 69 and 52 samples have one native
calibrated-BP age claim. Their native age endpoints differ from the published
series-end labels by at most 0.5 years numerically, but the source chronology
labels and age support do not establish a common selected chronology. The
[generated interpretation](REPORT.md) keeps the sample and category context;
the [manifest](manifest.json) binds all source inputs and results.

The producer uses the governed prerequisite projection and a
[two-sample independent count-mass receipt](count-mass-crosscheck.json)
extracted from the earlier source audit. Its scientific JSON fields reproduce
the earlier working result exactly; only the input identities changed. Run
from the repository root into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_lake_core_correspondence \
  --raw-part data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json \
  --raw-manifest data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json \
  --workbook data/landclim/raw/landclim_ii_site_metadata.xlsx \
  --workbook-receipt data/landclim/raw/landclim_sources.json \
  --count-mass docs/report/source-relations/neotoma/swedish-lake-core-identity/count-mass-crosscheck.json \
  --projection docs/report/source-relations/neotoma/lra-prerequisites/projection.json \
  --output artifacts/swedish-lake-core-identity/replay
```

The separate [Bussjösjön basin review](../bussjosjon-basin/README.md) retains
the 2.5264 km conflict with a later inventory point. Neither nearby LandClim
metadata point resolves that discrepancy. No LRA sample, source right or
original pollen denominator is admitted by this comparison.
