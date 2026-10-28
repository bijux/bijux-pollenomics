# Author example site-mean pollen holdout

The [source-pinned result](report.json) withholds each of 17 author site IDs
within its grid, then predicts each available 31-taxon pollen composition from
the equal-site mean at the same time bin. It scores 177 of 184 observed site-bin
targets and refuses seven bins without another training site. Site-macro mean
absolute error is 0.018949 in fraction units; site-macro total variation is
0.293703. The [score ledger](scores.csv) retains each scored or refused bin,
and the [prediction ledger](predictions.csv) retains taxon predictions.

This is an untuned, previously exposed development baseline. It is separate
from the later model search, which compares candidates on 174 common bins.
The different scored support prevents a direct improvement claim. Site IDs
lack reviewed aliases across databases; the prepared 31-taxon axis is not a
closed raw-core denominator. No LRA skill, Swedish transfer or measured
vegetation accuracy follows from this result. Original author inputs and the
independent R reference remain in private source custody with redistribution
unresolved.

The [result](report.json) binds the author source revision and private reference
receipt to the scored denominators and method. The [prediction](predictions.csv)
and [score](scores.csv) ledgers are the retained numeric outputs. The
[family replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py) checks the private source identity, runs the existing
producer, normalizes its two CSV line endings and verifies all four tracked
outputs. From the repository root, use an absent output directory under
`artifacts/`:

```sh
.venv/bin/python docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/author-example-site-mean-holdout/replay
```

The governed [report](report.json) and [generated summary](REPORT.md) retain
the current result. The producer emits CRLF CSV while these retained ledgers
use LF; the replay changes only those line endings before the byte comparison.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** An untuned leave-one-author-site-ID-out within-grid baseline predicts the equal-site mean of available training pollen fractions at the same bin. Retained site-macro MAE is 0.018949 fraction and total variation 0.293703 on scored support.

**Unsupported claim.** An independent selected-model improvement, a spatial-block evaluation, Swedish LRA/transfer or vegetation accuracy, calibrated uncertainty, reviewed cross-database aliases or certified raw-core grain denominator/redistribution rights.

**Actual verification performed.** Executed the maintained advertised family replay on local main at cacf5c5d956f379cf21b94b64791e1daf7650f1a, including the unchanged observed-pollen site-ID holdout producer, and an independent complete four-product/source observer; both native stages exited zero. All 193 original author snapshot members were authenticated. Final report.json, scores.csv, predictions.csv and the fully managed REPORT.md were byte-identical to the governed family. CSV CRLF-to-LF conversion preserved every cell, and verified_authored_reader/render_route authenticated the original prose and current footer. This reader retains its own authored body. Support remains17sites/2grids/31taxa,184 observed site-bin targets,177 scored and7 refused; no new R, ecological model, rights or human acceptance is claimed.

**Remaining input or review.** Author outcomes were previously exposed; site IDs lack reviewed cross-database alias closure. Prepared 31-taxon counts and within-site correlated bins are not a complete raw-core denominator or independent uncertainty sample. Independent vegetation truth and intended redistribution rights remain unbound.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Interpret this as the untuned observed-pollen baseline on its own 177-bin support. The later search’s 174 common bins and the buffered study’s 148/140 bins are different evaluation supports, so their aggregate MAEs are not a direct paired improvement claim.

**Precise next acceptance route.** Compare methods only on explicitly identical scored targets, qualify physical groups/aliases and full source/use scope, and freeze a new evaluation before previously unexposed outcomes. Admit measured vegetation and LRA inputs separately for ecological claims.

**Negative or refused result.** 7 of 184 observed site-bin targets lack another same-bin training site and remain refusals; zero-count bins are unavailable, not scored zeros. Different support prevents direct comparison with the selected development search.

**Matched denominator.** 17 English author site IDs in 2 grids;31 prepared taxa;184 observed site-bin targets;177 scored and 7 refused. Site-macro scores weight the 17 site-level mean errors equally after averaging correlated bins within each site.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-example-site-mean-holdout/report.json](report.json) (SHA-256 `a18e74cf74a3891c54b8496918290cb8028968261c55c9a782fe2b9848e3b2ca`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-example-site-mean-holdout/scores.csv](scores.csv) (SHA-256 `baf477c6a5389699d247e0d2a1e3055fd3d2a4454142c46eb9c6f0148f1e5797`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-example-site-mean-holdout/predictions.csv](predictions.csv) (SHA-256 `ef41a225f53f55323144457d377f87ebc719df1e329fb607a30a5c16470db84d`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
