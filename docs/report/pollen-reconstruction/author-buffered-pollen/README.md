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
include those diagnostics. The [family replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-buffered-pollen/replay.py) rebuilds the local
site mean, four methods on both grids, scores and five comparisons from the
private author capsule. It checks the declared source and producer identities,
then compares all 51 generated files to this tracked family. From the repository
root, use an absent output path under `artifacts/`:

```sh
.venv/bin/python docs/report/pollen-reconstruction/author-buffered-pollen/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/author-buffered-pollen/replay
```

The baseline and taxon comparison outputs must match byte for byte.
The local site-mean producer's
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
