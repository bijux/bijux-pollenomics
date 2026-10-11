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

The baseline and taxon comparison directories retain the same current v3
comparison, including site, block and taxon diagnostics. The earlier v1
baseline contained the same method summaries and score receipts but did not
include those diagnostics. To replay the source-bound family from the repository
root, use an absent output directory under `artifacts/`:

```sh
SOURCE_ROOT=../bijux-pollenomics-data/landclim/author-reference
OUT=artifacts/author-buffered-pollen/replay
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src

.venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.observed_pollen_baseline \
  --author "$SOURCE_ROOT/author" --reference "$SOURCE_ROOT/reference" \
  --run docs/report/publication-replay/landclim-method-profile/reference \
  --output "$OUT/local-site-mean"

for spec in training-mean:training_mean nearest-site:nearest_site \
  inverse-distance-squared:inverse_distance_squared \
  fitted-clr-rbf:clr_rbf_ridge_half_count; do
  family=${spec%:*}
  method=${spec#*:}
  for grid in 512 562; do
    .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial \
      predict --author "$SOURCE_ROOT/author" --reference "$SOURCE_ROOT/reference" \
      --output "$OUT/$family/grid-$grid" --target-grid "$grid" --method "$method"
  done
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial \
    score --author "$SOURCE_ROOT/author" --reference "$SOURCE_ROOT/reference" \
    --output "$OUT/$family/scores" \
    --prediction-512 "$OUT/$family/grid-512" \
    --prediction-562 "$OUT/$family/grid-562" \
    --local-scores "$OUT/local-site-mean/scores.csv"
done

.venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.comparison \
  --training-mean "$OUT/training-mean/scores" \
  --nearest-site "$OUT/nearest-site/scores" \
  --inverse-distance-squared "$OUT/inverse-distance-squared/scores" \
  --output "$OUT/comparisons/baseline"
cp -R "$OUT/comparisons/baseline" "$OUT/comparisons/taxon"
.venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.hellinger_comparison \
  --comparison "$OUT/comparisons/baseline/report.json" \
  --training-mean "$OUT/training-mean/scores" \
  --nearest-site "$OUT/nearest-site/scores" \
  --inverse-distance-squared "$OUT/inverse-distance-squared/scores" \
  --output "$OUT/comparisons/hellinger"
.venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.fitted_comparison \
  --training-mean "$OUT/training-mean/scores" \
  --nearest-site "$OUT/nearest-site/scores" \
  --inverse-distance-squared "$OUT/inverse-distance-squared/scores" \
  --clr-rbf-ridge-half-count "$OUT/fitted-clr-rbf/scores" \
  --output "$OUT/comparisons/fitted-common-support"
.venv/bin/python docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/strict-clr-support/replay.py \
  --author "$SOURCE_ROOT/author" --reference "$SOURCE_ROOT/reference" \
  --output "$OUT/comparisons/strict-clr-support"
```

The current v3 baseline output also supplies `comparisons/taxon`. Its two files
must match `comparisons/baseline` byte for byte. The local site-mean producer's
`scores.csv` must hash to
`644ca0bd0049f0fe682b75fa24bca1ab9b9a456de3cb4704c2976f33d1c974c9`.
The tracked within-grid score ledger has normalized line endings and a
different byte hash, so it cannot replace that producer output when scoring
the buffered blocks. The private source capsule must match the manifest's
`private_source_manifest_sha256` before comparing family output bytes.

This result concerns direct observed-pollen prediction under a specific
English spatial split. It neither evaluates LRA reconstruction nor supplies
Swedish basin geometry, measured vegetation truth or publication rights. Its
fixed fitted configuration is distinct from the later three-fold development
search and cannot be used as an independent estimate of that selected model's
skill.
