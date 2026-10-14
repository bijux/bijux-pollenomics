# Joint site, count and PPE REVEALS draws

The [bounded result](report.json) reuses the two heterogeneous basins and
source-bound deposition factors in the [fixed-site covariance
example](../fixed-site-covariance/README.md). It retains **2,048** explicit
paired replicates: [original-site indices and count/PPE draws](draws.json) and
the resulting [closed cover draws](joint-cover-draws.csv). The report SHA-256
is `ab16d5edfffb56d2377782e75857d0f60ab76b19563d38ed2563d5af8a634152`.
Each draw file has its own SHA-256 and byte count in the report. The declared
seed is a reproduction aid; the retained arrays are the draw identities.

For each replicate, the site index row samples the two **original physical
sites** with replacement. Each original site has one multinomial count draw
with its observed total; choosing a site twice reuses that site's count draw
and geometry twice. One positive correlated PPE vector is shared by the two
selected site entries. Counts are divided by their own site's deposition
factor before pooling, then by the shared PPE and closed to fractions. The
reported mean is the arithmetic mean of closed replicate covers. This
definition differs from the historical R release's ratio of accumulated
unclosed weights. The synthetic fixture marks all three taxa as measured at
both sites; the API refuses any unresolved not-measured taxon rather than
converting it to an observed zero.

| Paired scenario | A SE | B SE | C SE |
| --- | ---: | ---: | ---: |
| Joint site, count and PPE | 0.056571 | 0.165329 | 0.173418 |
| Fixed sites, count and PPE | 0.056494 | 0.030819 | 0.067913 |
| Site only | 0.001429 | 0.163347 | 0.161918 |
| Count only | 0.034142 | 0.022232 | 0.040662 |
| PPE only | 0.046005 | 0.021218 | 0.055877 |

The fixed-site count/PPE draw SEs are close to the independent first-order
delta example's 0.055315, 0.029472 and 0.067454, within Monte Carlo sampling
variation. The paired ablations reuse the same arrays and geometry but their
variances are **not additive components**. With only two sites, site resampling
has just four possible site-index patterns; these numbers demonstrate the
calculation and a sensitivity, not a population interval or ecological skill.
Chronology, basin geometry and transport remain fixed, and no source-qualified
lake or pollen sample is admitted by this synthetic result.
The [author raw/prepared taxon comparison](../../source-relations/landclim/author-example-taxon-support/README.md)
shows why the retained 17 real author sites cannot simply use an all-measured
31-target mask in this reviewed profile.
The [restricted author-site calculation](../author-site-uncertainty/README.md)
therefore selects only ten taxa with positive counts at all six sites in one
window and reports its separate closed-subcomposition uncertainty.

The [calculation](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py)
requires explicit arrays and refuses changed site totals, invalid identities,
nonpositive PPE or malformed axes. The three focused tests check duplicate-site
handling, paired count/PPE changes, and refused invalid draws.

Replay all three governed files into `artifacts/` and compare them byte-for-byte:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python \
  docs/report/method-certification/joint-site-draws/replay.py \
  --repository . --output artifacts/joint-site-draws/replay
cmp docs/report/method-certification/joint-site-draws/report.json \
  artifacts/joint-site-draws/replay/report.json
cmp docs/report/method-certification/joint-site-draws/draws.json \
  artifacts/joint-site-draws/replay/draws.json
cmp docs/report/method-certification/joint-site-draws/joint-cover-draws.csv \
  artifacts/joint-site-draws/replay/joint-cover-draws.csv
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The retained synthetic account propagates 2,048 explicit paired draws across site resampling, counts for each original site and correlated shared positive PPE, while duplicated site selections reuse the same original-site count draw.

**Unsupported claim.** The four paired ablations do not define additive variance components, and these conditional draws do not certify field coverage, historical R correspondence, chronological or geometry uncertainty, or measured vegetation accuracy.

**Actual verification performed.** Reviewed the draw rules, retained scenario summaries and exact report bytes, including the mismatch between its historical fixed-site source-report hash and the current fixed-site report. No draws or model calculations were regenerated for this qualification.

**Remaining input or review.** The configured joint-draw owner must replay against the qualified current fixed-site report and preserve the original-site coupling. Scientific use needs measurement and parameter justification and independent assessment of omitted uncertainty.

**Cause category.** Conditional paired resampling with a historical dependency mismatch.

**Consequence.** Shared-site and PPE dependence can dominate selected taxa; neither differing ablation SEs nor increasing replicate count establishes scientific validity or current-source correspondence.

**Precise next acceptance route.** Replay fixed-site covariance first, then joint-site draws with explicit input arrays and measurement refusals; compare all five native scenarios and preserve nonadditive interpretation before scientific review.

**Negative or refused result.** Unresolved measurement remains refused. The joint SEs 0.056571,0.165329,0.173418 exceed some fixed-site components; this is retained rather than explained away as failure or improvement.

**Matched denominator.** Two synthetic sites, three taxa,2,048 paired replicates and five scenario summaries; only four ordered site-resampling patterns are possible with two draws from two sites.

Qualified authored reader SHA-256: `9cd5a57be09afe51b577c5e1f1b731288aea332ac03d569ca13647754ff5481b`.

- [Retained qualification evidence: docs/report/method-certification/joint-site-draws/report.json](report.json) (SHA-256 `ab16d5edfffb56d2377782e75857d0f60ab76b19563d38ed2563d5af8a634152`).

- [Retained qualification evidence: docs/report/method-certification/joint-site-draws/draws.json](draws.json) (SHA-256 `75acab9c92bc36f94209ffba8e0bd1b69716f78b45a2e43c25673ecea88beca6`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
