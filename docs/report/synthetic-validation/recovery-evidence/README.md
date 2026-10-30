# Independent synthetic recovery and counting diagnostics

The [retained account](report.json) brings together the eight-case
[public REVEALS reconstruction challenge](../reconstruction/README.md) and
three conditional counting experiments. The account producer reads exact
immutable numerical products; it does not rerun transport, reconstruction or
simulation. [The counting packet](source-files/finite-count-coverage/manifest.json)
retains its protocol, all actual synthetic count draws, all replicate/taxon
results and the independent review.

The reconstruction challenge was freshly executed on source candidate
`0179bc4fe37e4928776eb07a793f769aef680da2`. All eight public `run_reveals`
attempts were scored and passed their predeclared calculation contracts. Its
output is byte-identical to the retained report
`5023c8d46e58680492ce3bc821d1db6ff10af1c0ad7f7bb75907aa3562e19e84`.
The generator imports only standard library modules, and the execution checked
that both the generator and public consumer came from the frozen owned source.

Six runs use two independently implemented GPM peatland cases, each with matched
parameters, a broadleaf PPE multiplied by `0.8`, and a cyclic taxon-label shuffle.
These share the production method's equations and are inverse crime controls
for calculation correctness. Two further cases use a different finite-cell
inverse-square forward model and preserve its mismatch with the production GPM
transport/support assumptions. Their truth MAEs are `0.0674633333333333` and
`0.07989669750321703` vegetation fraction. Passing the calculation contract
preserves these errors; it does not establish recovery of that different model's
truth. The maximum calculation discrepancy is `4.864424231990072e-6`, within
the declared `5e-6` rounding tolerance, and the maximum deposition discrepancy
is `5.551115123125783e-17`, within the declared `1e-12` absolute tolerance.

The counting experiments were executed at their original source candidate
`2b076418e86577058f70db216783ae3b2b74040b`. Each retains 1,000 independently
sampled multinomial draws on six fixed synthetic supports and ten taxa. The
count probabilities use the protocol's fixed deposition, PPE and synthetic
vegetation truth. The production fixed-site covariance consumer uses a measured
boolean mask, zero PPE covariance and fixed site geometry. These are synthetic
counts in a development fixture, not observed source counts or independent
field vegetation measurements.

| Counting experiment | Attempts / accepted | Preserved interval outcome |
|---|---:|---|
| Uniform vegetation, matched transport | 1,000 / 1,000 | Per-taxon coverage ranges from 934/1,000 to 963/1,000 |
| Rare Alnus truth (`0.00001`), matched transport | 1,000 / 1,000 | Alnus covers 427/1,000; 525 draws have zero pooled count and zero standard error |
| Uniform vegetation, assumed Alnus deposition multiplied by 1.5 | 1,000 / 1,000 | Alnus covers 0/1,000; bias is `-0.030951302160679012` |

The reported intervals are unclipped marginal normal intervals with multiplier
`1.959963984540054`. Compositional closure makes their simultaneous interpretation
inappropriate. The full account preserves every taxon's coverage numerator,
denominator, Monte Carlo standard error, bias, RMSE, empirical variance, mean
plug-in variance and zero-count/zero-standard-error frequency, including the
poorer outcomes. There were no refused counting draws. The matched counting
experiments share the inverse model; they are conditional numerical controls.
The named transport misspecification is a deliberate sensitivity, not a measured
transport error.

The separate independent review recomputed cover and marginal counting variance
from all 3,000 retained draws: 60,000 scalar comparisons across 30,000 marginal
rows. Maximum differences were `5.551115123125783e-17` for cover and
`5.421010862427522e-20` for variance. The review binds all four source products
and preserves the poor outcomes. The earlier production spot checks cover only
25 draws per experiment and remain distinct from this complete retained review.

These diagnostics establish independent forward generation, noise-free numerical
contracts, noisy conditional coverage measurements and explicit model
misspecification cases. They do not certify interval coverage, generalize to
unseen support/model choices, estimate PPE uncertainty, resample sites, validate
chronology uncertainty, establish ecological accuracy, or supply global method,
rights, human-review or release acceptance.

Rebuild the deterministic retained account from an installed development package:

```bash
python -m bijux_pollenomics_dev.lra_validation.recovery_evidence \
  --repository . \
  --output artifacts/science/synthetic-recovery-evidence/report.json
cmp docs/report/synthetic-validation/recovery-evidence/report.json \
  artifacts/science/synthetic-recovery-evidence/report.json
```

The original eight-case producer and its independent generator remain available
through the linked reconstruction challenge. The source packet's immutable
hashes reject changed report, draw, marginal-row and review bytes; retaining this
account does not authorize relabelling historical results as a fresh study.

## Maintained numerical reproduction

The maintained counting producer was executed against numerical source candidate
`159d541e7b86442728b9d540ebec93588eba54eb` using the exact prepared producer
code recorded in the [execution custody](source-files/finite-count-coverage/execution-custody.json).
That producer/verifier code was an artifact proposal at execution time and is
identified by its own physical hashes; it was not already tracked in that baseline
commit. The new native consumer completed in `7.57752462499775` seconds; the
independent complete scalar verification completed in `0.9345254999934696` seconds.
Both native exits were zero and all 156 registered input pins remained unchanged.

Every generated multinomial draw and all 30,000 marginal CSV rows exactly match
the original study bytes. Every scientific report field also matches. Only the
fresh execution's candidate and plan hash differ, and both original and fresh
reports are retained separately. The fresh scalar verification again reproduces
the reported maximum differences and all poor outcomes. Runtime/source/native
log identities, the exact numerical source closure and original/fresh execution
distinctions are retained in the custody packet. No source R program was replayed.

To repeat the fixed numerical experiment, supply the actual source revision and
SHA-256 of your separately frozen execution plan, and choose absent artifact
destinations. The source protocol retains its original preparatory metadata and
local source locator as historical bytes; the maintained producer instead uses
explicit repository/protocol/output arguments and the adjacent immutable source
report to validate the fixed support, taxa, PPE and deposition.

```bash
python -m bijux_pollenomics_dev.lra_validation.counting_coverage \
  --repository . \
  --protocol data/synthetic-validation/finite-count-coverage/protocol.json \
  --output artifacts/science/counting-recovery/products \
  --source-candidate <full-source-revision> \
  --plan-sha256 <frozen-execution-plan-sha256>
python -m bijux_pollenomics_dev.lra_validation.counting_coverage_verification \
  --repository . \
  --protocol data/synthetic-validation/finite-count-coverage/protocol.json \
  --products artifacts/science/counting-recovery/products \
  --output artifacts/science/counting-recovery/independent-review.json
```

The verifier uses only the standard library. It recomputes each scalar quotient
and marginal multinomial quadratic form from the retained counts, rather than
calling the production inverse or covariance code. The full draw and marginal
rows make numerical and missingness counterexamples available to tracked-only
readers without rebuilding an unrelated source capture.


## Fixed-response two-taxon counting intervals

A separate public API, `fixed_two_taxon_counting_interval`, now provides a
Clopper–Pearson binomial confidence set for **one fixed-N aliquot and exactly
two measured taxa with fixed known positive response/PPE**. Its monotone
response transform gives complementary cover bounds. This is a new declared
conditional profile: it does not change or certify the ten-taxon Wald intervals
above, incorporate uncertain PPE or transport, or establish ecological accuracy.

The [actual account](two-taxon-counting.json) retains 10,809 intervals covering
every count k=0..N for eight N values (1, 2, 5, 10, 25, 50, 100 and 1,000),
three confidence levels (0.8, 0.95 and 0.99), and three fixed response/PPE
scenarios. The independent Decimal observer checked 4,068 scalar endpoint and
transform comparisons and 6,102 root-containment conditions. Maximum absolute
discrepancy was `2.7184810473274716e-16`, below the frozen `2e-13` comparison
threshold; the distinct `1e-65` containment precision was retained. All 1,080
finite-grid coverage populations retain every k outcome, including rare pollen
probabilities of 1e-8 and 1e-5. Two extra outward memberships remain visible.
These finite checks supplement the conditional binomial argument; they do not
turn the declared grid into an empirical vegetation validation.

SciPy supplies inverse seeds only. Directed Decimal tails certify each accepted
probability bound against the exact binary64 confidence tail. Outward bracketing
and bisection on the representable-float lattice have an explicit 128-evaluation
bound per endpoint; the largest observed count was 19 evaluations. Decimal
range-loss traps and N<=10,000 limit work and numerical range. Exact rational
response/PPE transforms and comparison-directed conversion enclose each cover
and its complement. Unmeasured taxa, extra sample axes, invalid counts,
nonpositive parameters, numerical range loss and uncertifiable requests refuse.

At N=1,000, k=0 and confidence 0.8 with equal response, the first-taxon cover
point is zero while its upper bound is `0.002299936177446683`. Thus this profile
does not collapse a measured zero count to a zero-width confidence set. The
previous refused N=1,000/k=494 seed now yields pollen bounds
`[0.47326125258832163, 0.5147563571785784]` with accepted-request tail certificates.
The [execution custody](two-taxon-counting-source.json) preserves both earlier
native failures: one-ULP padding failed root containment at N=5/k=2, and 128
adjacent-float adjustments could not certify the later SciPy seed. Neither
failure is removed or relabelled as a passed study.

The maintained producer and standard-library-only observer retain exactly the
executed source bytes. To repeat the declared profile on an admitted LRA runtime,
choose absent artifact output files and supply the actual installed LRA source
root for the producer's import-origin check:

```bash
python -m bijux_pollenomics_dev.lra_validation.two_taxon_counting \
  data/synthetic-validation/two-taxon-counting/protocol.json \
  artifacts/science/two-taxon-counting-intervals.json \
  /path/to/installed/bijux_pollenomics_lra/source-root
python -m bijux_pollenomics_dev.lra_validation.two_taxon_counting_verification \
  data/synthetic-validation/two-taxon-counting/protocol.json \
  artifacts/science/two-taxon-counting-intervals.json \
  artifacts/science/two-taxon-counting-independent-review.json
```

The [retained numerical packet](source-files/two-taxon-counting/manifest.json)
preserves the exact protocol, compressed full interval rows, complete independent
coverage review and the prior negative account. Each raw numerical product has
its own physical hash. This public API does not model shared PPE uncertainty,
site resampling, heterogeneous pooling, chronology probability or more than two
taxa; the existing covariance APIs and their original failures remain separate.


## Exact finite-law covariance check

A separate deterministic check measures the approximation in the fixed-site
delta-covariance profile. Two constructed sites have independent binomial
counts with totals 3 and 4 and first-taxon probabilities 1/3 and 1/2. Their
fixed response rows are `(1, 2)` and `(3, 1)`. The nominal PPE vector is
`(1, 2)`. One law keeps PPE fixed; the other independently chooses the shared
vector `(9/10, 21/10)` or `(11/10, 19/10)` with equal probability. The same
chosen PPE vector applies to both sites, with covariance
`[[1/100, -1/100], [-1/100, 1/100]]`.

The [finite-law control](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-lra/tests/unit/reconstruction/uncertainty/test_finite_covariance_law.py)
enumerates every count/PPE outcome using exact fractions: 20 outcomes with
fixed PPE and 40 with shared PPE. Their probabilities sum exactly to one.
For each outcome, it closes the two corrected count weights directly, then
computes the exact mean and covariance of that estimator. Separately derived
rational scalar derivatives check the public API's first-order counting,
shared-PPE and total covariance at the expected counts `(1, 2)` and `(2, 2)`.
The original recorded software check used an absolute `1e-15` bound with zero
relative tolerance. Its 42 covariance-module controls passed in 0.10 seconds.
That historical run recorded Git HEAD
`fffb52cb1fd7f73e67b68066f290cf6f6a91f5e4`, with the finite-law controls in the
working tree and its production covariance consumer unchanged from
`1134c3697`. These are the original run's scope and source identities, not a
fresh reconstruction or a current-parent qualification receipt. The separate
finite-law module retains the two constructed questions and every original
numerical assertion; the existing fixed-site covariance and mask controls
remain in their own module.

| Constructed law | Outcomes | Exact expected first fraction | Estimate at mean inputs | Exact first-coordinate variance | Delta variance |
|---|---:|---:|---:|---:|---:|
| Fixed PPE | 20 | 0.503649550312 | 0.526315789474 | 0.043540623186 | 0.042034668242 |
| Shared PPE | 40 | 0.504362482759 | 0.526315789474 | 0.044307585677 | 0.043433138174 |

Nonlinear closure separates the expected estimator from the estimate at mean
inputs. In these two laws, the exact variance exceeds the delta variance by
0.001505954944 and 0.000874447503. Complementarity determines the second
coordinate and the negative off-diagonal covariance. Agreement with the
independent first-order calculation verifies the declared API; it does not
make that approximation equal to the exact finite-distribution moments.
This control adds no numerical algorithm or tolerance change.

These are constructed estimator laws, with no physical vegetation truth,
estimated PPE distribution, transport calculation, Monte Carlo sampling or
field data. They establish no interval coverage, ecological calibration or
whole-requirement acceptance. The retained reconstruction and counting
products above keep their original scopes and bytes.

Run the two finite-law controls from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -B -m pytest -q --rootdir=packages/bijux-pollenomics-lra \
  -c configs/pytest.ini -p no:cacheprovider \
  --basetemp="$PWD/artifacts/qualification/finite-covariance-law/pytest" \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/uncertainty/test_finite_covariance_law.py
```

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Eight independent synthetic generation cases and three fixed-site multinomial counting studies preserve noise-free calculation contracts, explicit forward mismatch and all noisy coverage outcomes. A separate exactly-two-taxon fixed-response binomial profile certifies accepted-request probability tails and complementary rational cover bounds.

**Unsupported claim.** General multinomial or simultaneous multi-taxon interval coverage, uncertain PPE/response, site-bootstrap or repeated-sample uncertainty, chronology calibration, ecological accuracy, historical reproduction or release approval.

**Actual verification performed.** Fresh eight public REVEALS attempts match the retained challenge bytes. Complete independent scalar review checks all 3,000 draws and 60,000 cover/variance quantities; maintained reproduction preserves every draw and 30,000 marginal rows exactly. The separate API executes 10,809 intervals; independent Decimal checks 4,068 numeric quantities, 6,102 root containment conditions and 1,080 all-k finite coverage populations at unchanged thresholds.49 API guards pass; all frozen source/runtime inputs remain unchanged.

**Remaining input or review.** Independent generation and exact numerical contracts are established, while empirical marginal coverage fails for rare counts and misspecified transport; finite-cell forward truth is not recovered by the different inverse model. The new exact binomial profile is conditional on exactly two measured taxa, fixed counting effort and fixed known response/PPE; it does not resolve the original general multi-taxon or misspecified-response failures. Resolver: Independent statistical uncertainty and transport-model reviewer Reopen when: A new frozen known-truth protocol qualifies the intended count, support, parameter and transport population before outcomes are evaluated.

**Cause category.** assumption|algorithm/numerical|comparability

**Consequence.** A passed calculation contract preserves truth errors and poor coverage; conditional marginal normal intervals cannot be promoted into simultaneous or ecological certification. Conditional binomial coverage and accepted-request numerical certificates apply only to the declared two-taxon population; the ten-taxon poor outcomes and ecological limits remain.

**Precise next acceptance route.** Use the supported exactly-two-taxon fixed-response profile only within its declared conditions. For uncertain PPE, additional taxa, heterogeneous or repeated samples, independently freeze and verify another inference model; preserve the prior rare-count and misspecified-response failures.

**Negative or refused result.** Rare Alnus intervals cover 427/1,000; 525 zero-count draws have zero standard error. Misspecified Alnus deposition gives 0/1,000 coverage. Two distinct finite-cell forward cases retain truth MAEs 0.0674633333333333 and 0.07989669750321703. The two-taxon predecessors retain native exit 1 root-containment and bounded inverse-seed refusals before the final lattice-certified successor passes; no field observations were evaluated.

**Matched denominator.** Eight reconstruction attempts: six same-equation controls and two distinct finite-cell models. Three counting cases each have 1,000 draws, six fixed synthetic sites and ten taxa; 30,000 marginal rows and 60,000 independent scalar comparisons. Separate two-taxon study: 10,809 intervals/eight N values/three confidence levels/three fixed-response scenarios, 4,068 numeric comparisons/6,102 containment checks/1,080 finite all-k coverage populations.

Retained evidence: [docs/report/synthetic-validation/recovery-evidence/report.json](report.json), [docs/report/synthetic-validation/recovery-evidence/source-files/finite-count-coverage/manifest.json](source-files/finite-count-coverage/manifest.json), [docs/report/synthetic-validation/recovery-evidence/source-files/finite-count-coverage/independent-review.json](source-files/finite-count-coverage/independent-review.json), [docs/report/synthetic-validation/recovery-evidence/two-taxon-counting.json](two-taxon-counting.json), [docs/report/synthetic-validation/recovery-evidence/two-taxon-counting-source.json](two-taxon-counting-source.json), [docs/report/synthetic-validation/recovery-evidence/source-files/two-taxon-counting/manifest.json](source-files/two-taxon-counting/manifest.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
