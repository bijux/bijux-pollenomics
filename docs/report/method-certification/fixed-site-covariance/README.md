# Fixed-site REVEALS covariance example

The [replay](replay.py) evaluates a separately named
`reveals-fixed-site-delta-covariance-v1` profile for two synthetic sites with
different basin types and radii. It uses the existing source-bound GPM
deposition implementation for a 75 m peatland and a 300 m lake, then combines
three taxon count vectors with a shared PPE vector and its **full covariance**.
The [machine result](report.json) retains the counts, physical parameters,
deposition factors, component covariance matrices, source-file identities and
declared limitations. The result SHA-256 is
`8b7c137687ab1b964a698463456ebe6fd656840b9fa3ff88942f83804827f9fa`.

For taxon $i$, the unclosed weight is
$w_i = \sum_s n_{si}/(K_{si} p_i)$, and the cover is $w_i/\sum_j w_j$.
The delta method propagates independent fixed-total multinomial counts within
each fixed site and the full covariance of the shared PPE vector. Counting and
PPE components are reported separately; their covariance matrices add to the
conditional total. Every output is a fraction, with standard errors in
fraction units. Site selection, age, basin geometry and transport uncertainty
are held fixed. The example explicitly marks every taxon as measured at both
sites; the API refuses an unmeasured taxon rather than treating it as zero.

| Taxon | Fixed-site cover | Counting and PPE SE | Counting-only SE |
| --- | ---: | ---: | ---: |
| A | 0.187169 | 0.055315 | 0.033854 |
| B | 0.098380 | 0.029472 | 0.022439 |
| C | 0.714451 | 0.067454 | 0.040933 |

The off-diagonal PPE terms contribute to this example; replacing the full
matrix with its diagonal changes the reported covariance. The focused tests
also check the independent two-site binomial limit, covariance closure and
taxon-permutation invariance. The historical publication-source implementation
remains separate and continues to reproduce its pinned R outputs. Its site
bootstrap is a different uncertainty estimand and cannot be replaced by these
conditional standard errors.

The source GPM lake expression carries an unresolved comment in the author's
release. Reusing it here tests covariance arithmetic under declared factors;
it does not certify lake transport physics, chronology, PPE applicability,
empirical skill or corrected site-resampling uncertainty. A joint site,
counting, parameter and chronology analysis remains necessary for full
multi-site certification.

Replay into `artifacts/` and compare the result byte-for-byte:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python \
  docs/report/method-certification/fixed-site-covariance/replay.py \
  --repository . --output artifacts/fixed-site-covariance/replay
cmp docs/report/method-certification/fixed-site-covariance/report.json \
  artifacts/fixed-site-covariance/replay/report.json
```
