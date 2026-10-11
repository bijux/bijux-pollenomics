# Current native R reference execution

The [retained result](report.json) is a fresh R 4.6.0 execution of the source-locked DISQOVER 0.9.14 package against the current Python implementation. All **43 core cases** and **23 source-domain cases** passed with zero failed cases. The 43 include 18 prospective optimized LOVE cases for three declared fixtures, including intermediates, taxon/ring axes, wrapper replay, and nonfinite/refusal behavior. The original 25 core cases and all 23 source-domain cases also agree with the [original authenticated R bundle](../original-r-reference/reference-bundle/certificate.json): **48/48** paired R vector comparisons pass under their original tolerances. The largest absolute difference between the original Linux R and current native macOS R vectors is `3.552713678800501e-14`.

The [core raw results](oracle/report.json), [domain raw results](source-domains/report.json), executed R scripts, case manifests, supplied inputs, session details, and every R output vector are retained here. [The current R producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference.py) checks the exact source lock, R version, native base and installed dependency versions, five missing source archive hashes, and the bundled DISQOVER source hash. It installs the missing packages into an isolated artifact library, executes the actual R runners, and verifies the current Python/R input file hashes before and after. Its command receipt lists only the explicit numerical environment settings needed to reproduce the run.

The five exact dependency archives are preserved in the private Pollenomics source store with SHA-256 and byte counts in [the report](report.json). Provider URLs and pinned archive versions are in the repository's [source lock](../../../../configs/ci/lra-r-source-lock.v1.json). The reference DISQOVER archive and license notices remain in the [LRA package](../../../../packages/bijux-pollenomics-lra/NOTICE). The runner can also retrieve those same locked archives from the provider, validating bytes before installation.

## Reproduction

Set `BIJUX_LRA_SOURCE_CACHE` to a directory containing the five pinned source archives and run from the repository root with an absent output below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.lra_validation.live_reference \
  --repository . --output artifacts/jobs/native-r-reproduction \
  --r /usr/local/bin/R --rscript /usr/local/bin/Rscript \
  --fortran /opt/homebrew/bin/gfortran --source-cache "$BIJUX_LRA_SOURCE_CACHE"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.lra_validation.live_reference_comparison \
  --repository . --run artifacts/jobs/native-r-reproduction \
  --original docs/report/method-certification/original-r-reference/reference-bundle \
  --output artifacts/jobs/native-r-comparison \
  --private-sources "$BIJUX_LRA_SOURCE_CACHE"
```

The [comparison producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py) validates original certificate closure, every current source hash and command result, exact private archive custody, full case denominators, and cross-platform R vectors before retaining the raw results. Strict mypy and Ruff checks passed for the two producers; the actual R and comparison commands returned zero.

## Optimized LOVE objective and bounded search

The current [solver](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/optimization/solver.py)
and [optimized reconstruction](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/optimized.py)
match the source SHA-256 values bound in this report's `current_inputs_sha256`.
The focused [solver checks](../../../../packages/bijux-pollenomics-lra/tests/unit/optimization/test_solver.py)
and [optimized-profile checks](../../../../packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_optimized_profile.py)
passed **70/70** on this source state. They cover fixed-candidate objective replay,
independently derived interior and boundary optima under eight seeds each,
distinct cover vectors with the same optimum, exact evaluation budgets and
nonconvergence, bounded custom result certification, and a LOVE consumer's
forward-pollen and objective values. The 18 prospective R cases additionally
check declared optimized intermediates and supplied-candidate wrapper behavior.

Recheck the focused Python consumer selection from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m pytest -q \
  -o cache_dir=artifacts/jobs/love-optimizer-acceptance/cache \
  --basetemp=artifacts/jobs/love-optimizer-acceptance/tmp \
  packages/bijux-pollenomics-lra/tests/unit/optimization/test_solver.py \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_optimized_profile.py
```

## Scientific and release boundary

This is current native macOS R execution with exact package source versions. It is **not** the separate locked Linux release certificate: the interpreter and platform identities differ, and this output does not claim a full Linux runtime/library file closure or release authorization. The prospective replay cases test agreed objective and wrapper behavior under supplied candidates; they do not establish stochastic optimizer trajectory parity, a global optimum, uncertainty calibration, ecological prediction accuracy, or independent vegetation truth. Those remain separate acceptance requirements.
