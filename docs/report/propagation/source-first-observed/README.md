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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The retained source-readiness screen preserves all native variables, sample missingness and two explicit chronology profiles for Neotoma sites 12 and 3009, with zero admitted first-observed events.

**Unsupported claim.** It estimates no ecological change time, first appearance, propagation edge, empirical threshold or accepted whole-pollen feature by relabeling a native variable.

**Actual verification performed.** Read native site/sample denominators, profile decisions and overlapping blocker counts in the retained report; bound its bytes. No source download, screen or estimator was rerun.

**Remaining input or review.** Every attempted variable lacks an accepted taxon-concept mapping; unreported observations and noncomparable, refused or overlapping chronology still prevent complete ordered event support.

**Cause category.** Native observation and chronology admission refusal rather than missing values imputed as absence.

**Consequence.** The zero-event result retains all requested attempts and cannot be promoted to ecological absence or a four-country event census.

**Precise next acceptance route.** Qualify one exact native variable and accepted concept under a reviewed named chronology, retain null cells and all age refusals, and invoke the public estimator only on complete definitely ordered comparable support.

**Negative or refused result.** All 256 attempts refuse and the public event estimator is invoked zero times. Native default ages are context-only; the alternative includes four refused site 12 claims and remaining interval-order uncertainty.

**Matched denominator.** Site 12: 135 samples, 2580 positive observations, 58 variables; site 3009: 28 samples, 523 positive observations, 70 variables. Two profiles×128 variables=256 attempts; 14 full-coverage attempts represent seven variables twice, not 14 independent events.

Qualified authored reader SHA-256: `d2cee2a8542f37336a1c1065367579787e6751f095cd295475309c0cac000fa6`.

- [Retained qualification evidence: docs/report/propagation/source-first-observed/report.json](report.json) (SHA-256 `dfa81aec856e4fd253d3435095c9dfa54a470ca102b34b7d250ab82a266c599d`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
