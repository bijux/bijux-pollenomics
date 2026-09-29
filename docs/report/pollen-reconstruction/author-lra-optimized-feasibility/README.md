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

[report.json](report.json) retains the request identities, count denominator,
budgets and refusal outcomes. [prepare.py](prepare.py) rebuilds and validates
both exact request bytes from the private 193-file author source capsule, without
depending on an `artifacts/` cache. Its output request SHA-256 values must match
the report. The source-backed preparation was replayed successfully. Numerical
execution was performed at product commit `83e3b4119` with one thread and the
wall limits in the report; the host surfaced `optimizer_nonconvergence` in both
attempts. The [process custody receipt](custody.json) binds the two original
design declarations and refusal logs to exact bytes in the private source store;
all 20 selected request/evidence files matched a fresh source-based replay.
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
