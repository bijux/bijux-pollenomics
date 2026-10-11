# Preparing forward pollen deposition

`prepare_forward_inputs(params, rings, regional_cover, config)` prepares a
target basin's numerical inputs without target pollen, a target total count,
an optimizer or random draws. The result feeds `forward_deposition`:

```python
from bijux_pollenomics_lra.api import ForwardConfig, prepare_forward_inputs, forward_deposition

prepared = prepare_forward_inputs(
    parameters, target_rings, regional_cover,
    ForwardConfig(local_ring_count=2, local_basin_diameter_m=20),
)
prediction = forward_deposition(
    predicted_local_cover,
    prepared.regional_deposition,
    prepared.local_k,
    prepared.terrestrial_fraction,
    prepared.ppe,
)
```

The host supplies independently predicted local vegetation, exact taxon order,
target geometry, parameter lineage and a training-derived regional background.
It records site/time/geometry/source identities and excludes held-out outcomes.
The engine prepares numerical arrays; it does not select a spatial estimator or
make an ecological acceptance decision.

## Method identity and source disposition

The `preparation_profile`
`disqover-0.9.14-corrected-matrix-homogeneous-v1` preserves the taxon axis when
there is one local or regional ring. This is an explicit matrix interpretation
of the deposition equation, separate from literal R LOVEoptim's dimension-drop
and recycling behavior. The legacy optimized reconstruction profile continues
to refuse those unsupported source dimensions. Corrected forward preparation
does not relax the legacy profile's restrictions.

Dispersal factors reuse the audited `calK` and source weighting functions.
As in the source, ring integration uses peatland geometry and wind 3m/s. The
basin shore is represented by explicit ring boundaries. No standalone diameter
factor or training-basin kernel is silently reused. The local and regional
deposition sum reuses the engine's existing matrix equation.

## Inputs and units

`params` requires unique, nonempty string `Taxon` values, `fallspeed` in m/s
(source range 0.01–0.15), positive `ppe` and nonnegative `ppe.error`. All numeric
inputs must be finite actual numbers; booleans and numeric strings are refused.
PPE is nominal in both local and regional deposition. PPE SD is retained in the
input contract but is not sampled by this preparation.

`rings` requires `inner`, `outer`, and `mean` in metres, `ring` and `terrestrial`
in square metres. The initial `circular-shore-contiguous-v1` geometry requires
ordered nonoverlapping contiguous circular annuli, the first inner radius equal
to the declared basin radius, mean within each interval, and geometric annular
area agreement (relative and absolute tolerance 1e-8). Terrestrial area lies in
[0, ring area]. At least one positive local terrestrial contribution and at
least one explicit regional ring are required. A zero terrestrial regional
remainder is explicit zero deposition. The finite outer support cannot exceed
100km; no deposition beyond that support is invented.

Narrow rings can produce negative source GPM factors. These geometries raise
`unsupported_forward_kernel_geometry`; values are not clipped. Central water,
gaps, partially straddling shore rings and other GIS profiles require separate
reviewed geometry admission.

`regional_cover` is shape `(taxa,)` in parameter order. The default
`closed-fractions` profile requires sum one within absolute tolerance 1e-12.
Explicit `disqover-rounded-fractions` permits the source's rounded reconstruction
closure error, `number_of_taxa * 0.000005 + 1e-12`. Entries remain in [0,1] and
are preserved without renormalization. Percentages are never inferred. Local
cover supplied to `forward_deposition` remains a closed fraction vector.

## Result and uncertainty boundaries

`PreparedForwardInputs` exposes `taxa`, `local_k` `(local_rings,taxa)`, local
`terrestrial_fraction`, `ppe` and already PPE-weighted `regional_deposition`.
It also retains full K/fractions, ring bounds, supplied regional cover,
distance-weighting/profile identities and finite outer support. Every array
has independent immutable backing. Relative kernel mass is neither an absolute
pollen flux nor a predicted count.

The interface accepts one explicit regional vector and performs no RNG work.
For uncertainty, the caller preserves draw identity and ancestry while pairing
regional and local-cover draws. Regional vectors can already contain upstream
REVEALS variation; adding independent PPE resampling here would change source
semantics. This profile does not claim chronology, basin, spatial, parameter
covariance or full joint uncertainty propagation.

## Reference evidence

The existing 25-case oracle remains a separate suite. The additional runner
`tests/reference/lra_oracle/run_source_domains.py` reports 23 individually named
cases: source wrapper/ring refusals, safe zero-support and supplied-regional
exceptions, and corrected forward profiles across five kernels, two basin
sizes, single-ring boundaries and explicitly rounded regional composition.
Preparation-only reports never claim live R execution. Candidate replay tests
the source wrapper and objective inputs, not optimizer convergence or empirical
land-cover accuracy.

Host `ForwardInputs.method_profile` must use `prepared.method_profile`, which
remains `disqover-0.9.14-homogeneous-local-forward` and agrees with the existing
`ForwardResult.method_profile`. Persist `prepared.preparation_profile` separately
with geometry lineage; the preparation identity is not the observation-model
identity. Neither identifier is silently relabeled.
