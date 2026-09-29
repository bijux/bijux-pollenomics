# Buffered author-pollen spatial comparison

The author-prepared English cohort has 17 site IDs, 31 named pollen taxa and
two adjacent withheld one-degree grids (512 and 562). The frozen rule removes
training sites whose reported basin edges are within 20 km of any target site
in the withheld grid. Predictions use only opposite-grid training counts;
scoring reads target counts after each grid's predictions are saved. These are
previously exposed development outcomes, not a confirmatory validation cohort.

The three fixed baselines share 148 of 184 observed site bins; 36 have no
buffered same-bin training site. On this support, inverse-distance squared has
site-macro MAE 0.025217, nearest site 0.025285 and the training mean 0.025303.
Their site-level and 31-taxon diagnostics are in the
[taxon comparison](comparisons/taxon/REPORT.md). The corresponding Hellinger
distances are 0.356682, 0.362546 and 0.357926 respectively; the
[Hellinger ledger](comparisons/hellinger/REPORT.md) retains the 148 paired bins.

The fixed CLR radial-basis fit adds one half-count per named **training** taxon,
uses the median positive training-site distance as its length scale, and uses
ridge penalty 0.01. It scores 140 site bins; eight additional bins require two
training sites. On the common 140-bin support, its site-macro MAE is 0.040564,
versus 0.025298 for the training mean. The
[four-method comparison](comparisons/fitted-common-support/REPORT.md) contains
the paired result and both block summaries. A separate
[strict-positive CLR support diagnostic](comparisons/strict-clr-support/REPORT.md)
found no bin in either block where all 31 taxa were positive in every eligible
training count vector. That diagnostic did not fit or select a model.

Each method directory retains both grid predictions, statuses, source and model
receipts, observed-count scores and per-taxon scored predictions. The
[manifest](manifest.json) binds every output byte, source manifest identity and
producer modules. The private author source capsule is authenticated in the
[main study custody record](../author-source-custody.json); no raw author files
are redistributed here.

To recompute a comparison from the retained scores into an artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.fitted_comparison \
  --training-mean docs/report/pollen-reconstruction/author-buffered-pollen/training-mean/scores \
  --nearest-site docs/report/pollen-reconstruction/author-buffered-pollen/nearest-site/scores \
  --inverse-distance-squared docs/report/pollen-reconstruction/author-buffered-pollen/inverse-distance-squared/scores \
  --clr-rbf-ridge-half-count docs/report/pollen-reconstruction/author-buffered-pollen/fitted-clr-rbf/scores \
  --output artifacts/author-buffered-pollen/fitted-comparison
```

The installed prediction and scoring entry point is
`bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial`; it accepts
`predict` or `score` with a private `--author` and `--reference` capsule. Its
separate comparison, Hellinger and fitted-comparison modules consume the
retained score directories. The strict CLR diagnostic can be reproduced with
`comparisons/strict-clr-support/replay.py` and the same private capsule.

This result concerns direct observed-pollen prediction under a specific
English spatial split. It neither evaluates LRA reconstruction nor supplies
Swedish basin geometry, measured vegetation truth or publication rights. Its
fixed fitted configuration is distinct from the later three-fold development
search and cannot be used as an independent estimate of that selected model's
skill.
