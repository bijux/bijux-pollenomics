# Synthetic spatial eligibility

[Retained consumer report](report.json) records fabricated coordinates and BP
intervals passed through the public WGS84 pair evaluator and regional network
generator. Country labels and ages are fixtures; these are not historical routes.

## Independent truth and prospective contract

The threshold is fixed at 100 km and 100 years. Equatorial longitude is constructed
with the standard library from `degrees(distance_metres / 6378137)`, using the WGS84
semimajor axis. This is an independent equatorial arc calculation, without a
geodesic forward call. Distance agreement tolerance is `1e-11 km`; scientific
threshold comparison has **zero tolerance**. The declared exact-boundary fixture
allows at most 32 adjacent binary64 longitude adjustments to obtain an inverse
result exactly equal to 100 km. This run needed zero adjustments. The construction
is explicit and does not establish independence from every WGS84 model assumption.

All 18 requested pair/input attempts remain in the report: 12 evaluated pairs,
three pair refusals, two event ingestion refusals, and one fixture range refusal.
All 18 contract checks passed. Four regional events produce 12 evaluated oriented
pairs: three definite candidates and nine nonpositive temporal exclusions. The
northern SE source finds all three declared NO, FI, and SE neighbors. Indexed and
exhaustive candidate edge identities agree.

## Retained numerical results

| Case | Full inverse distance, km | Status |
|---|---:|---|
| Inside threshold | 99.999999 | definite candidate |
| Exact threshold | 100.0 | definite candidate |
| One millimetre outside | 100.000001 | excluded spatially |
| Four tenths of a millimetre outside | 100.00000040000002 | excluded spatially |
| Malmö to Lund fixture | 16.18861101448624 | definite candidate |
| SE/FI outside fixture | 222.63898158654712 | excluded spatially |
| Distinct site IDs at identical coordinates | 0.0 | definite candidate, shared location |

Both outside boundary cases display as `100.0 km`; the smaller also rounds to
`100.000000` at six decimal places. Their full binary64 eligibility values survive
JSON persistence with identical hexadecimal representations. Every evaluated
pair retains the distance algorithm, library, and library version. The nominal
independent `100.0000004 km` truth is realized by the pinned inverse calculation
as `100.00000040000002 km`, not the literal binary64 value `100.0000004`.

The older NO and younger SE fixture gives an eligible cross-border arrow at an
exact 100-year lag. Swapping country labels retains distance, lag bounds, status,
and arrow eligibility. Overlapping SE/DK intervals retain lag bounds `[-150, 50]`
and emit no arrow. Missing chronology retains null bounds and unresolved status.
Lag 101 years is excluded; bounds `[90, 110]` retain possible candidate status.

Missing paired coordinates produce `invalid_or_missing_coordinate` in the pair
refusal output. A partially present coordinate preserves its reported axis and
null missing axis at ingestion, then produces the same pair refusal.
Invalid latitude and longitude also fail ingestion. Two events from the same
governed site produce `same_governed_site`, with no candidate. A legal numerical
axis reversal fails the independently declared Nordic fixture box; general WGS84
range validation alone cannot detect every axis reversal.

## Reproduction and coverage limits

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.spatial_eligibility_challenge \
  --output artifacts/jobs/synthetic-validation/spatial-eligibility/report.json
cmp docs/report/synthetic-validation/spatial-eligibility/report.json \
  artifacts/jobs/synthetic-validation/spatial-eligibility/report.json
```

This result supports spatial eligibility and regional country-neutral candidate
selection. Country-only map context and focal-country display counts require a
separate display consumer. It does not validate real source coordinates, source
admission, empirical ecological accuracy, or full numerical method parity.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Known constructed method/identity challenge; no empirical biological accuracy or untouched confirmation.

**Supported claim.** Constructed WGS84 and age-boundary cases preserve exact numerical eligibility, country-neutral pair status and indexed/exhaustive neighbor correspondence under fixed 100 km/100 year thresholds.

**Unsupported claim.** This tests neither real source coordinates and chronology, empirical ecological thresholds, country-only display counts nor full numerical method parity.

**Actual verification performed.** Read all requested/evaluated/refused categories and full-distance versus display-rounding examples; bound the report. No inverse geodesic, regional search or fixture calculation was rerun.

**Remaining input or review.** Actual coordinates need source provenance and axes review; historical pair ages and feature ownership need independent admission before ecological use.

**Cause category.** Constructed spatial/chronology software boundary contract.

**Consequence.** A displayed 100.0 km value cannot replace the persisted full binary64 value in scientific eligibility, and an arrow remains a fixture result.

**Precise next acceptance route.** Use admitted source coordinates and comparable chronology, preserve full precision through persistence, and separately exercise the actual display consumer for map-count claims.

**Negative or refused result.** Both just-outside cases remain excluded although their displays round to 100.0 km; missing coordinates, invalid axes, same governed site and unresolved ages retain explicit refusals or non-arrow status.

**Matched denominator.** Eighteen requested attempts: twelve evaluated pairs, three pair refusals, two ingestion refusals and one fixture refusal. Four regional events produce twelve oriented pairs, three candidates and nine nonpositive-time exclusions; all eighteen contract checks pass.

- [Retained qualification evidence: docs/report/synthetic-validation/spatial-eligibility/report.json](report.json) (SHA-256 `d100b2a53fb840533a7c44b28ee78caa1769464a61c34c969c741333fa9b0e70`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
