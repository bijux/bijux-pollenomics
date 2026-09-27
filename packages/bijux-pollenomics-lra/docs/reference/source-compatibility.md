# DISQOVER 0.9.14 source compatibility

This package separates **source-compatible behavior** from any later scientific
revision. Changes to the conventions below require a new algorithm identifier
and independent parity baseline.

## Dispersal

- LSM fall speeds are rounded using R-compatible decimal rounding before model
  selection.
- Serialized LSM models do not extrapolate outside their fitted domain.
- GPM and lake calculations retain the source package's diameter/radius calling
  conventions; they are not normalised behind the caller's back.
- `1overd` is retained because it is an active source option, although it is not
  interchangeable with a mechanistic dispersal model.

## REVEALS

- Cover is rounded to three decimals at the draw level before summaries.
- Summary order and sample standard deviation match the source wrapper:
  mean, median, 90th percentile, 10th percentile, sample SD.
- The Python API permits deterministic and supplied-draw execution for testing;
  these are explicit extensions, not claims about the R default RNG stream.

## Analytical LOVE

- Rings are valid only where `inner > local_diameter / 2`, matching the source's
  strict inequality.
- Regional and local K arguments differ in the source and remain distinct.
- Estimates are not clipped or renormalised after regional subtraction.
- The source spelling `OutlierQant` remains in the compatibility return object.

## Optimised LOVE

- `calK` forces the peatland deposition path because DISQOVER 0.9.14 marks the
  corresponding lake-ring path unresolved.
- The terrestrial/geometric area correction is retained.
- The source samples a local PPE vector but does not use it in the objective;
  Python compatibility preserves this rather than silently changing the model.
- The observed local pollen vector receives `+0.001` inside log distance without
  subsequent renormalisation.
- Cover is rounded to four decimals and modeled pollen percentages to two before
  wrapper summaries.

## Optimisers

SciPy differential evolution is a Python backend, not a reimplementation of
RcppDE/DEoptim. Compare model objectives on common candidates separately from
convergence behavior. `ReplayOptimizer` exists for that purpose.

A supplied optimizer must return a finite vector within the original box, a
finite objective, nonnegative iteration count, positive search evaluation count
and boolean success. The boundary owns the returned vector and independently
evaluates the deterministic objective on it before LOVE publishes reconstructed
cover, modeled pollen or objective summaries. The reported and evaluated values
must agree within `1e-12` absolute and relative tolerance. That tolerance is fixed
for this boundary and does not replace the declared R oracle tolerances.

The independent certification evaluation is separate from the backend's reported
search evaluation count (`nfev`); replay keeps its candidate count. Certification
preserves a backend's failure status and does not establish global optimality or
convergence parity. `tests/unit/optimization/test_solver.py` checks invalid
solutions, immutable original bounds, retained failure diagnostics and a complete
LOVE consumer with a symmetric known cover and forward pollen expectation.
