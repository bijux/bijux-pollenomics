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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The declared 20 km buffered split supports three fixed observed-pollen baselines on 148 common site-bins and a separate fixed half-count CLR/RBF fit on 140; strict-positive support without replacement is absent. Reported method/metric differences are descriptive on those exact supports.

**Unsupported claim.** Untouched confirmation, Swedish LRA vegetation reconstruction, independently measured vegetation accuracy, general long-distance transfer skill, calibrated spatial confidence intervals or cleared publication/redistribution rights.

**Actual verification performed.** The original family retains ten historical producer pins and 54 file-index entries; nine numerical producer files and all 51 compared authored/numeric payload identities remain unchanged. An actual bounded no-fit consumer invoked the maintained _compare on those 51 retained source-produced payloads and returned zero differences; 19 source-free guards passed. Exact managed blocks and every pinned public evidence file are authenticated before stripping only the owned terminal block. No raw source preparation, predictions, fitting, scoring or R execution was repeated; current full end-to-end domain replay remains separately unexecuted.

**Remaining input or review.** The 20 km basin-edge rule does not independently close pollen-source footprints or cross-database aliases. Two adjacent previously exposed English blocks do not establish independent transfer uncertainty. Full raw-core grain denominators, matched vegetation observations, intended-use rights and qualified scientific review remain unbound.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Read these observed-pollen outcomes as descriptive development evidence on their stated support. Do not convert their errors or source identity into vegetation, LRA, independent confirmation or general-transfer accuracy.

**Precise next acceptance route.** For a new general-transfer claim, qualify source identity/footprints/aliases, raw denominators and rights, then freeze a development-selected protocol before scoring genuinely untouched independent spatial groups. A vegetation/LRA claim additionally needs admitted basin/chronology/taxon support and independently matched vegetation truth; obtain qualified review of that exact estimand.

**Negative or refused result.** The fitted common-support MAE 0.040564 is poorer than training mean 0.025298. Strict-positive CLR admits 0 fits in both grids;36 baseline and 44 fitted targets remain unscored. Different supports must not be pooled.

**Matched denominator.** 17 English author site IDs;31 named taxa;2 adjacent one-degree grids 512/562;184 observed of 425 possible site-bins. Baselines 148/184 with 36 missing-training refusals; fitted 140/184 with 36 missing-training plus 8 insufficient-training refusals. Strict CLR diagnostic spans 25 bins per withheld grid.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json](manifest.json) (SHA-256 `5b243b240ba16b3523fe679aed97860e506a15bbf781c84a215b22e9edca3c60`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/baseline/report.json](comparisons/baseline/report.json) (SHA-256 `e3fe6ba62e1983dddb4b1f1a324e96979a8b60c3d4416110e864a70c2d0ced1a`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/fitted-common-support/report.json](comparisons/fitted-common-support/report.json) (SHA-256 `8c9d218fd294cfbe485a153d1e635f953146e408bd5aa31321e2cf1b4036754a`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/strict-clr-support/report.json](comparisons/strict-clr-support/report.json) (SHA-256 `82696876e0890c5f3b0973156b9d1dc0f74d2b28faad8980574333ab6a75981a`).

- [Retained qualification evidence: reports/science/buffered-pollen-reader-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/buffered-pollen-reader-custody.json) (SHA-256 `0ed06d48124ca7335a8ebfdf959c9b8ef5f0871ccbc82d1bc340fea1fec5b403`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
