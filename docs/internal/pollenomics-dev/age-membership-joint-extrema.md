# Joint endpoints of marginal pooled-count bounds

This diagnostic asks whether the endpoints of independently calculated time-bin
bounds can share one possible age per source sample. Its numerator is the
observed closed 16-taxon pollen NISP; its denominator is all native pollen NISP.
It does not estimate vegetation cover. It retains the source-reported marginal
age intervals, including negative younger limits as evidence. Those limits are
not admitted canonical dates. The analysis bins remain nonnegative and half open.

## Exact criterion

Let a bin's compulsory pooled counts be `(N, D)` with `D > 0`, and let optional
sample `i` have counts `(n_i, d_i)` with `d_i > 0`. For a subset `S`, its pooled
fraction is `(N + sum(n_i))/(D + sum(d_i))`. All arithmetic uses exact integers
and rational fractions.

At the minimum `L`, an optional sample whose fraction `n_i/d_i < L` must be
included: otherwise adding it strictly lowers the pooled fraction. A sample with
`n_i/d_i > L` must be excluded: otherwise removing it strictly lowers the
fraction. The positive compulsory denominator makes both operations valid.
At the maximum `U`, the inequalities reverse. Samples exactly equal to the
target fraction are neutral.

These requirements are sufficient as well as necessary. Start from an extremizing
subset, which exists because there are finitely many optional subsets. Every
strictly required inclusion and exclusion agrees with that subset by the previous
argument. Any remaining differences involve only neutral samples. Adding or
removing a sample satisfying `n_i = L*d_i` preserves `N = L*D`, and likewise for
`U`. The compulsory denominator keeps the fraction defined.

Apply these requirements to every requested bin endpoint. The bins are disjoint,
so a source sample required in two different bins makes the corner impossible.
Otherwise intersect its closed native age interval with its remaining allowed
bin locations and the complement of all analyzed bins. An empty intersection is
another impossibility witness. If every sample has a nonempty intersection, choose
one age independently from each intersection. Those choices satisfy all bin
requirements, hence all requested endpoint fractions simultaneously. No coupling
between sample ages is assumed.

The implementation deliberately refuses bins without positive compulsory mass.
If a bin can be empty, neutral-sample choices across bins require an additional
nonempty-allocation constraint. This diagnostic makes no claim for that case.

## Retained ABBO source accounting

The consumer binds the existing 107-row age/count support, the 428-row membership
ledger, the original marginal-bound report, and their declared raw source,
configuration, manifest, replay and helper identities. It recalculates the
memberships and exact marginal fractions before assessing joint endpoints.
The original per-bin bounds and interval-contained products remain unchanged.

There are four bins and 16 lower/upper endpoint combinations. Every combination
has at least one source-sample impossibility witness. For example, sample
`neotoma:sample:173201` has native age support `[2261,2640]` and count fraction
`482/1088 = 241/544`. At bin 4's lower endpoint `2283/6823`, this sample must be
excluded because its fraction is larger. At bin 5's upper endpoint `5103/11483`,
it must also be excluded because its fraction is smaller. These adjacent bins
cover that entire native age interval. The sample has nowhere else to go, so
those two endpoints cannot coexist in one allocation.

Five source-native intervals have negative younger bounds. They lie outside the
analyzed positive bins and remain unchanged. Possible-age witnesses are
mathematical witnesses, not reconstructed chronologies or measured sample ages.

## Verification and interpretation

The independent fixture oracle partitions each native interval at every bin
boundary, enumerates endpoints and interior representatives, and exhausts all
resulting sample allocations. It compares both marginal extrema and joint corner
attainability to the threshold implementation, including neutral ties, adjacent
and separated bins, closed right endpoints, native negative evidence and exact
large counts. Publication tests cover retained-ledger identity, malformed and
duplicate fields, missing sources, source drift and absent artifact outputs.

These results diagnose compatibility of count-fraction extrema conditional on
marginal source support. They are neither joint confidence statements nor age
probabilities. Depth monotonicity, dependence between calibrated ages, revised
prediction, vegetation inference, source rights and scientific admission remain
outside this diagnostic. The individually attainable marginal bounds remain valid.
