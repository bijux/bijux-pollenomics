# Fixed-input homogeneous likelihood

`bijux_pollenomics_lra.api.fit_homogeneous_likelihood` fits a separately named
conditional point estimator. It does not replace the optimized LOVE profiles.
The caller supplies matching observed weights, positive local coefficients
`a`, and nonnegative fixed regional deposition `b`, on the same ordered taxon
support and deposition units. For homogeneous local cover across rings,
`a_i = PPE_i * sum_r(K_ri * terrestrial_fraction_r)`. Geometry and parameters
remain the caller's declared inputs.

For closed nonnegative cover `v`, the forward composition is
`p_i = (a_i*v_i + b_i) / sum_j(a_j*v_j + b_j)`. Write `B = sum(b)` and let
`Y_ji = (a_i*delta_ji + b_j)/(a_i+B)`. The simplex transformation
`lambda_i = v_i*(a_i+B) / sum_j(v_j*(a_j+B))` gives `p = Y @ lambda`.
Its inverse is the normalized vector `lambda_i/(a_i+B)`.

The mean negative log likelihood `-sum(q_i*log(p_i))`, for normalized
observed weights `q`, is convex in `lambda`. Zero observed weights need no
pseudocount. Actual integer counts give a multinomial sampling interpretation;
fractional weights define the same point objective without establishing its
sampling uncertainty. The function does not infer unmeasured taxa as zeros.

A feasible matrix inverse supplies an exact-composition candidate. Otherwise,
bounded pairwise simplex steps move mass between taxa, minimizing along each
direction. Each scalar root search allows at most 100 iterations. `max_steps`
limits the number of pairwise moves, including an explicit zero-step diagnostic.
Results retain actual steps, stop reason, observed mass, condition number,
objective and the declared gap tolerance. Result arrays are owned and read-only.

For gradient `g`, `g @ lambda - min(g)` bounds remaining objective
suboptimality in exact arithmetic. `converged` checks its floating-point value;
it is not an interval-arithmetic certificate or a vegetation-error bound.
The returned candidate remains inspectable after budget exhaustion. Callers
must check `converged` before accepting numerical completion. Invalid aggregate
mass, underflow, nonfinite diagnostics and unstable composition conversion
refuse execution. Vertices exceeding `max_condition_number` are refused;
the default is `1e12`. Raising that limit changes the numerical contract and
does not establish identifiability.

This profile holds regional deposition, PPE, kernels and terrestrial fractions
fixed. It supplies no joint PPE uncertainty, lake-ring derivation, chronology
model, source-use permission or independent vegetation validation. A good
pollen fit can coexist with weakly identified vegetation, especially when
regional background dominates. Host workflows must bind source rows, counts,
taxon eligibility, physical cores, units and assumptions separately.
