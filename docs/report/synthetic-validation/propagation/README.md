# Synthetic derived-event propagation

[Retained report](report.json) consumes eight events from the public
`estimate_first_observed` sample estimator through the public
`run_propagation_sensitivity` network. One additional sample sequence with a
chronology gap is refused before network admission. The inputs are fabricated
equatorial coordinates, ages, and country annotations. They are not Nordic
occurrences or historical routes.

## Frozen truth and comparison

The fixture declares eight sample sequences at equatorial arc positions `0`,
`25`, `50`, `100`, `100.000001`, and `200 km`. Their point or interval ages are
recorded in the report's `prospective_contract.events`. Each sample carries its
own feature, family, snapshot, site, native count, unit, chronology, and evidence
identity. The selected event is a first observed **sample** event under
`reported_positive_v1`, not a global first appearance or ecological change time.

An independent standard-library calculation uses absolute differences of the
declared equatorial arc distances, with a fixed `6378137 m` WGS84 semimajor axis.
Expected lag bounds come from the declared endpoint arithmetic:
`source_younger - target_older` and `source_older - target_younger`. The report
compares these expectations with the production inverse geodesic and public pair
status, using `1e-11 km` only for numerical distance agreement. **Eligibility has
zero tolerance** at the 25, 50, 100, and 200 km and 50, 100, 200, and 500 year
maxima. No threshold was selected after observing the results.

The two aliases are explicit controls. An event with the older source's governed
site is refused as `same_governed_site`; a distinct site reusing the younger
source's observation IDs is refused as `duplicate_underlying_observation` for
that pair. The dependent alias can still form other candidate pairs under the
current pairwise rule; those edges are retained in the ledger and must not be
read as independent evidence of an additional biological occurrence.

## Retained outcomes

All **nine derivation attempts** remain visible: eight derived events and one
`chronology_unresolved` refusal. All **16 rectangular scenarios** were run.
Every ordered pair of the eight events was evaluated by the public pair API in
each scenario: `8 × 7 × 16 = 896` attempted pair decisions, with **896/896**
independent status, distance, chronology and annotation comparisons passing.
The complete pair ledger includes refusals and pairs outside the indexed search
envelope. The indexed network's reconciliation, IDs and directed edges are
retained separately. A conservative search envelope may evaluate a pair just
beyond a scientific threshold; its persisted status remains `excluded_spatial`.

| Distance maximum | Lag maximum | Directed candidates | Pairs outside indexed search envelope | Pair refusals |
|---:|---:|---:|---:|---:|
| 25 km | 50 years | 3 | 38 | 4 |
| 25 km | 100 years | 7 | 38 | 4 |
| 100 km | 50 years | 8 | 10 | 4 |
| 100 km | 100 years | 14 | 10 | 4 |
| 100 km | 500 years | 15 | 10 | 4 |
| 200 km | 500 years | 17 | 0 | 4 |

The report retains the other ten combinations too, plus each edge's count of
eligible scenarios. Under 100 km/100 years, the older NO to younger SE fixture
is definite at the 100-year temporal boundary. The 100 km NO to FI fixture is
possible with lag bounds `[80, 120]`; the 100.000001 km NO to DK fixture is
excluded spatially. FI to SE overlapping intervals are indeterminate and carry
no arrow. A 200 km pair with minimum lag 600 years remains excluded temporally
even under the 500-year maximum.

## Reproduction and scope

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.propagation_challenge \
  --output artifacts/jobs/synthetic-validation/propagation/report.json
cmp docs/report/synthetic-validation/propagation/report.json \
  artifacts/jobs/synthetic-validation/propagation/report.json
```

This challenge covers the declared whole-pollen positive profile and synthetic
pairwise topology. It does not validate all threshold profiles, ecological/taxon
hierarchies, source admission, real regional borders, empirical threshold choice,
or causal spread. Country labels are annotations in the fixture, not coordinate
claims about actual national territories.

A separate focused [network consumer check](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics/tests/unit/analysis/propagation/network/test_pair_evaluation.py)
uses fabricated older/younger pairs in seven feature universes spanning whole
pollen, group, subgroup, two roles and two taxa. The indexed network evaluates
only the 14 within-feature oriented pairs and emits seven forward candidates;
it does not enumerate cross-feature pairs. A direct pair with the same taxon
label but a different accepted concept ID is refused. This checks separation
logic only. Current source classification still admits no real propagation
event or edge for these ecological partitions.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Known constructed method/identity challenge; no empirical biological accuracy or untouched confirmation.

**Supported claim.** The fabricated sample-event network matches independently declared distance, lag, status and annotation expectations across all sixteen fixed rectangular sensitivity scenarios.

**Unsupported claim.** These equations and pairwise rules do not establish real Nordic routes, independent alias occurrences, ecological hierarchy validation, empirical thresholds or causal spread.

**Actual verification performed.** Read the full derivation and scenario denominators, boundary controls and retained alias limitations in the authored and machine reports; no network, source screen or numerical oracle was rerun.

**Remaining input or review.** Real-source classification currently admits no ecological event; accepted concepts, source chronology and scientific interpretation are required before historical propagation use.

**Cause category.** Constructed pairwise topology and threshold contract with explicit dependent aliases.

**Consequence.** The network can retain definite, possible, excluded and refused pairs without declaring those synthetic arrows historical or treating dependent aliases as new biology.

**Precise next acceptance route.** Admit a source-qualified event population, preserve feature ownership and observation ancestry, and run the actual public network with thresholds declared before scientific outcomes.

**Negative or refused result.** One derivation refuses chronology; same-site and duplicate-observation pairs refuse. A dependent alias can still form other pairwise candidates, which are retained without an independence claim.

**Matched denominator.** Nine derivation attempts yield eight events and one refusal; eight events×seven ordered partners×16 scenarios=896 pair attempts/comparisons. At 100 km/100 years there are 14 directed candidates, not 14 observed routes.

- [Retained qualification evidence: docs/report/synthetic-validation/propagation/report.json](report.json) (SHA-256 `6221c2efb076e2136b48d6d4330ab97aa407141d192b6efcd3478c2cc40e0540`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
