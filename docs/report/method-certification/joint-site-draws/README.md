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

The [calculation](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py)
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
