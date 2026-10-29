# Optimized LOVE feasibility on author pollen

The exact 31-taxon author-prepared LRA cohort uses a 0.006 m/s fall speed for
`Filipendula`; the available optimized LOVE profile admits fall speeds from 0.01
to 0.15 m/s. This separate exploratory pilot removes that taxon as an explicit
closed subcomposition. It removes 159 of 20,732 source counts (0.767%) across the
15 positive-count author sites. The selected training pair loses 42 regional
BECKHAM counts and 10 local LARKBARR counts. The original 31-taxon analytical
result and its negative local-cover rows remain unchanged.

The pair uses source-bound pollen counts, author PPE and fall speeds for the 30
remaining taxa, and the declared circular, fully terrestrial geometry. Two
local rings extend to 1,000 m; a third ring from the pinned forward geometry
extends to 10,000 m so optimized LOVE has regional support. The standard
fall-speed validation label is used for both operations because all retained
source values satisfy its bounds; the actual fall speeds and GPM-neutral distance
weighting are unchanged. Basin shape and land cover remain assumptions, not
authenticated historical landscapes.

Both validated requests refused numerically. With a cap of 40 iterations and
1,000 evaluations per run, all four optimized runs failed to converge. A second
bounded request allowed 120 iterations and 20,000 evaluations per run with one
repeat; both optimized runs failed to converge. These are caps, not claims that
every evaluation was consumed. No LRA product, held-out prediction or score was
published. The optimizer is SciPy differential evolution; its search trajectory
does not establish original R optimizer parity. Further tuning on these exposed
rows would be a new development study with a separate declared selection rule.

The pinned DISQOVER 0.9.14 source archive (`ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`)
uses RcppDE's returned `bestmem` and `bestval` without checking a convergence
flag. The pinned RcppDE 0.1.9 source archive
(`f48aeea87e379beb1a408aef11d65c3f2b8ce09e97c2add6f42f9446ea92fe3b`)
returns those fields and an iteration count, not a success field. This source
behavior justifies inspecting a finite best candidate, while the host's
convergence refusal still governs product publication.

The separate [finite-candidate diagnostic](finite-candidate.json) reruns the
unchanged extended request and coupled regional handoff, then reads the raw
optimized LOVE output before the product gate. Both local rings reached the
20,000-evaluation cap after 65 complete generations; neither converged. Their
best objective values were **6.9601** and **6.7633**, with forward-pollen mean
absolute errors of **4.3355** and **4.4585 percentage points** against the same
training local sample. The largest taxon error exceeded **62 percentage points**
in each ring. The finite cover vectors have no negative entries, but that does
not certify the search, make a held-out prediction, or replace the original
31-taxon analytical result. The [diagnostic producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite_candidate.py)
checks the exact request digest and revalidates its source evidence after the
calculation; it publishes no LRA product.

[report.json](report.json) retains the request identities, count denominator,
budgets and refusal outcomes. [prepare.py](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-lra-optimized-feasibility/prepare.py) rebuilds and validates
both exact request bytes from the private 193-file author source capsule, without
depending on an `artifacts/` cache. Its output request SHA-256 values must match
the report. The source-backed preparation was replayed successfully. Numerical
execution was performed at product commit `83e3b4119` with one thread and the
wall limits in the report; the host surfaced `optimizer_nonconvergence` in both
attempts. The maintained preparer verifies the private source manifest and
recreates the request/evidence inputs. Original process logs remain in the
qualified private source store; they are not needed to interpret this
negative result.

The preparation command is:

```sh
job=artifacts/jobs/author-lra-optimized-source-replay
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/pollen-reconstruction/author-lra-optimized-feasibility/prepare.py \
  --author-source-root /path/to/private/source/store/landclim/author-reference \
  --output "$job"
```

This one-pair negative feasibility result does not show that every optimized
budget fails. It does not supply source-backed Swedish lake geometry, an LRA
prediction, vegetation truth or a Nordic transfer estimate.

To reproduce the finite-candidate diagnostic after preparing the source-bound
requests into the absent job directory above:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite_candidate.py \
  --inputs "$job/extended/inputs" --output "$job/finite-candidate.json"
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Two explicitly bounded optimized-LOVE requests refuse convergence for one exposed English training pair. A separate finite-candidate diagnostic preserves best vectors/objectives without publishing a valid LRA product or held-out score.

**Unsupported claim.** Proof that every optimized budget fails, original R optimizer parity, a converged product, held-out skill, vegetation accuracy, source-authenticated Swedish geometry or Nordic transfer.

**Actual verification performed.** The retained request/refusal report, finite-candidate diagnostics and cited source behavior were inspected. Retained preparation reconstructs the exact private-source request digests; actual numerical execution is attributed to product `83e3b4119` and its recorded limits. This qualification launches no private preparation, differential-evolution run or forward fit.

**Remaining input or review.** The optimized profile excludes Filipendula because its 0.006 m/s source fall speed lies below the profile’s 0.01–0.15 m/s interval. Circular terrestrial geometry, source rights, physical/historical basin interpretation and external vegetation review remain separate; finite candidates do not resolve nonconvergence.

**Cause category.** assumption | algorithm/numerical | comparability | access/rights | qualified review

**Consequence.** Keep both bounded refusals and finite diagnostic vectors separate from publishable constrained cover. Further tuning on these exposed rows would be a new development study with its own fixed selection rule.

**Precise next acceptance route.** Declare a justified new optimizer/development protocol and bounds, preserve the same source/count/method identities and failed asks, then require its actual convergence/product gate before any prediction. Ecological or transfer claims additionally need independently admitted geometry/cohort/reference inputs.

**Negative or refused result.** The first request’s 4 runs and second request’s 2 runs all refuse convergence. Separate finite-candidate local-ring fits hit 20,000 evaluations without convergence, with forward MAEs 4.3355/4.4585 percentage points and maximum taxon error exceeding 62 points in each ring; no product or held-out score is accepted.

**Matched denominator.** One selected regional/local pair,30 retained taxa and 2 local rings. The wider 15-site source loses 159/20,732 grains to the explicit Filipendula exclusion; selected regional/local rows lose 42 and 10 grains. Budgets 40 iterations/1,000 evaluations versus 120/20,000 are caps, not claimed consumption.

Qualified authored reader SHA-256: `418f287cddc01d6b95f4d9e46751adb5b6a260e8a11f551ca428411ddf6e225d`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-optimized-feasibility/report.json](report.json) (SHA-256 `2d2202914ec86f70aad49d63782066c10a198997ef628f65d4e9134f2aefb869`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-optimized-feasibility/finite-candidate.json](finite-candidate.json) (SHA-256 `0de8b9f2558c60c8dd405c01a31cae6542f908e225aa28b698e7c645a2cc2cf1`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md) (source SHA-256 `1645884c253eec4ee079a5cfc7703a52f12516e20cfea2e5956ca646c16256ec`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
