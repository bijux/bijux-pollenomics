# Neotoma first-observed source readiness

This screen consumed the native Neotoma relational materialization for sites 12 and
3009 and checked each downloaded site export against the native part digests, row
identities, source snapshot, and reader build. The retained [report](report.json)
contains every source variable and sample cell, both predeclared chronology
profiles, every attempted feature/profile decision, and the verified input digests.
It is a source-readiness result, not an estimated first-observed event or route.

## Denominator and decisions

| Site | Samples | Positive native NISP observations | Variables | Variables reported at every sample |
| --- | ---: | ---: | ---: | ---: |
| Neotoma 12 | 135 | 2,580 | 58 | 2 |
| Neotoma 3009 | 28 | 523 | 70 | 5 |

All 128 source variables were screened under both `native_default` and
`named_calibrated_alternative` chronology profiles: **256 attempts, 256
refusals, zero admitted events, zero public-estimator invocations**. The 14
full-coverage attempts represent seven variables screened twice. An unreported
variable/sample cell is retained as `null`; it is not a zero or a confirmed
absence. NISP values remain native counts with their null source denominators.
The report keeps the site sample universe, both source age claims for every
sample, and one full sample inventory for each site variable. Each attempt
links to that inventory and retains all applicable refusal codes.

Native default age claims at both sites are uncalibrated and `context_only`
(135 and 28 claims). Site 12 has a separately named calibrated alternative
with 131 `comparable` claims and four `refused` claims; site 3009 has 28
`comparable` alternative claims. That alternative is a separate sensitivity,
not a publication chronology selection. Even full-coverage alternative series
have indeterminate adjacent age order where uncertainty intervals overlap.
For example, Betula and Pinus are reported at all 135 samples at site 12,
but their alternate series includes the four refused age claims and overlapping
age intervals. Betula, Pinus, Artemisia, Poaceae, and Cyperaceae are reported
at all 28 samples at site 3009, but alternate age intervals also overlap.

The verified export marks classification `not_accepted`, and the retained
source variable rows supply no accepted taxon-concept mapping. A single native
variable cannot be silently relabeled as
`whole:pollen` to satisfy the public event contract. Every attempt therefore
retains `accepted_taxon_mapping_not_available`; the diagnostic constructs
owned `GovernedSample` inputs only for reported rows with selected age claims
and never passes a fabricated event template to the public estimator. The
refusal counts in `denominators.blocker_counts` count applicable reasons per
attempt, so they overlap.

## Next admissible consumer

Qualify a source variable against an accepted taxon concept and a named,
reviewed chronology policy. Retain source-reported missingness, native NISP
measurement semantics and denominator status, calibrated interval overlap,
and all refused claims. A feature with complete reported observations,
comparable ordered ages, and that approved taxon ownership can then enter the
public first-observed estimator. This report grants no ecological accuracy,
propagation-route, or empirical threshold claim.

The [governed Nordic edge ledger](../governed-edge-ledger/README.md) retains the
16 ordered country reporting bins and original zero-event release evidence. It
keeps the two-site source denominator separate from four-country reporting
topology.
