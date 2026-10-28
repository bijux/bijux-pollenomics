# Fixed-site REVEALS covariance example

The [replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/method-certification/fixed-site-covariance/replay.py) evaluates a separately named
`reveals-fixed-site-delta-covariance-v1` profile for two synthetic sites with
different basin types and radii. It uses the existing source-bound GPM
deposition implementation for a 75 m peatland and a 300 m lake, then combines
three taxon count vectors with a shared PPE vector and its **full covariance**.
The [machine result](report.json) retains the counts, physical parameters,
deposition factors, component covariance matrices, source-file identities and
declared limitations. The result SHA-256 is
`ab9a44e76567d7a5e6841ec3e989c76bad9afc305388c8b837959e7c16e648d9`.

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

## Conditional composition and covariance identities

The [maintained covariance implementation](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py)
has the following algebraic properties for any declared panel of $m\geq2$
taxa and $S\geq1$ fixed sites. These properties concern its conditional
composition and first-order delta covariance.

Assume nonnegative integer counts $n_{si}$ with positive site totals
$N_s=\sum_i n_{si}$, finite positive deposition factors $K_{si}$ and PPE
values $p_i$, and a finite symmetric positive-semidefinite PPE covariance
$C_p$. For the source-observed profile, every supplied panel cell must have
resolved measurement support; an unreported source cell is not an observed
zero. Hold site selection,
chronology, taxonomy, geometry and transport fixed. Assume independent
fixed-total multinomial counts between sites and independence of counts
from the shared PPE vector. Pooling samples additionally assumes a common
conditional panel composition within each pooled window. These are model
conditions, not consequences of the algebra.

Write $b_{si}=(K_{si}p_i)^{-1}$, $w_i=\sum_s b_{si}n_{si}$,
$W=\sum_i w_i$ and $c_i=w_i/W$. Then $W>0$, $c_i\geq0$ and
$\sum_i c_i=1$: positive response/PPE parameters do not imply strictly
positive composition for a taxon with zero counts. Finite arithmetic also
requires representable weights and a finite positive normalizer; the
implementation rejects invalid corrected totals and requires every site's
integer count total to be below $2^{53}$.

Let $\mathbf1$ be the all-ones column vector and
$B=I-c\mathbf1^T$. Differentiating normalization gives
$dc=B\,dw/W$. Consequently the count Jacobian for site $s$ and the
Jacobian of the shared PPE vector are

$$
J_s=B\operatorname{diag}(b_s)/W,
\qquad
H=-B\operatorname{diag}(c_i/p_i).
$$

In components, $(J_s)_{ij}=(\delta_{ij}-c_i)b_{sj}/W$ and
$H_{ij}=c_j(c_i-\delta_{ij})/p_j$. The latter follows from
$\partial w_i/\partial p_j=-\delta_{ij}w_j/p_j$ even when several
sites share the PPE vector.

At the observed fractions $f_s=n_s/N_s$, the plug-in count covariance is
$C_{n_s}=N_s[\operatorname{diag}(f_s)-f_sf_s^T]$. Its multinomial
formula is exact at the unknown sampling probabilities; substituting
observed fractions estimates that covariance. Under the independence
conditions above, the reported first-order covariance is

$$
C_c=\sum_s J_sC_{n_s}J_s^T+HC_pH^T.
$$

For any vector $u$, with $\bar u_s=\sum_i f_{si}u_i$,
$u^TC_{n_s}u=N_s\sum_i f_{si}(u_i-\bar u_s)^2\geq0$.
Each count matrix is therefore positive semidefinite. Congruence preserves
this property because $v^TACA^Tv=(A^Tv)^TC(A^Tv)\geq0$;
the count, PPE and summed covariance components are positive semidefinite.
Also $\mathbf1^TB=0$, so $\mathbf1^TJ_s=\mathbf1^TH=0$.
Each component satisfies $C\mathbf1=0$ and $\mathbf1^TC=0$:
its row and column sums vanish and its all-ones direction is singular.
Additional zero-variance directions are possible. These are exact-real
identities. Implementation covariance checks and the separately retained
numerical closure checks use their declared floating-point tolerances.

For a single pooled panel with fixed total $N$, let $f=n/N$ and
$Z=\sum_i b_i f_i=W/N$. The fraction Jacobian is
$J_f=B\operatorname{diag}(b)/Z=N J_n$. Thus
$J_f[\operatorname{diag}(f)-ff^T]J_f^T/N
=J_nN[\operatorname{diag}(f)-ff^T]J_n^T$.
The fraction and count formulations used for two-, three- and six-taxon
panels have the same conditional counting covariance. A diagonal
$C_p=\operatorname{diag}(\mathrm{SD}_p^2)$ is a particular independence
assumption about PPE estimates; the general identity allows full $C_p$.

These identities do not prove the empirical multinomial assumptions,
source completeness, PPE transfer, physical factors or vegetation accuracy.
Panel closure is not closure over unparameterized taxa. At a zero-count
boundary the plug-in standard error can be zero without establishing an
absence interval. Shared PPE can correlate different windows or scenarios;
the individual covariance matrices are not a joint time-series model.
The delta approximation does not establish exact nonlinear sampling
uncertainty or confidence-interval coverage, historical reproduction,
chronology accuracy or the full LRA method contract.

Replay into `artifacts/` and compare the result byte-for-byte:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python \
  docs/report/method-certification/fixed-site-covariance/replay.py \
  --repository . --output artifacts/fixed-site-covariance/replay
cmp docs/report/method-certification/fixed-site-covariance/report.json \
  artifacts/fixed-site-covariance/replay/report.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The synthetic two-site, three-taxon account derives a first-order fixed-site delta covariance with shared full PPE covariance, separate counting and parameter terms, and closure/positive-semidefinite invariants under its declared domain.

**Unsupported claim.** The formula does not establish empirical interval coverage, site-selection, chronology, geometry or transport uncertainty, R parity, measured ecological accuracy or ecological absence from zero counts.

**Actual verification performed.** Reviewed the equations, retained three-taxon report and physical report identity; both declared producer/transport source hashes match current files. The authored reader cites a different historical report hash. This qualification ran no covariance calculation or original-R comparison.

**Remaining input or review.** The maintained owner replay must reconcile the stale reader report reference. A scientific case also needs valid finite parameters, measurement status and justified site and observation assumptions.

**Cause category.** Conditional mathematical covariance with a stale authored report reference; its two declared code dependencies currently match.

**Consequence.** The retained standard errors apply to fixed inputs and first-order propagation; they cannot be relabeled total physical uncertainty or a field calibration result.

**Precise next acceptance route.** Replay the fixed-site covariance owner, retain count-only and shared-PPE components, exercise finite positive parameter/integer count and measurement refusals, then obtain an independent scientific decision for the intended observations.

**Negative or refused result.** Unresolved taxon measurement, invalid parameters and unsupported count-domain inputs remain refusals; a zero observed count is not proof of absence or calibrated zero uncertainty.

**Matched denominator.** Two synthetic basins (75 m peat and 300 m lake), three taxa, count rows[30,20,50] and[20,65,15]; cover approximately 0.187169,0.098380,0.714451 with SE 0.055315,0.029472,0.067454.

- [Retained qualification evidence: docs/report/method-certification/fixed-site-covariance/report.json](report.json) (SHA-256 `bc4de9b4d9287128457598a611dccafa4eba4af4bb9e201488af130a16d4f38f`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
