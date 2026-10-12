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
