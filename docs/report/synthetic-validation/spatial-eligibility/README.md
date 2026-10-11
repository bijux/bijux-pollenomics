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
two pair refusals, three event ingestion refusals, and one fixture range refusal.
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
refusal output; a partially present coordinate is refused at event ingestion.
Invalid latitude and longitude also fail ingestion. Two events from the same
governed site produce `same_governed_site`, with no candidate. A legal numerical
axis reversal fails the independently declared Nordic fixture box; general WGS84
range validation alone cannot detect every axis reversal.

## Reproduction and coverage limits

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.spatial_eligibility_challenge \
  --output docs/report/synthetic-validation/spatial-eligibility/report.json
```

Selected checks passed: six direct consumer regressions, 12 existing spatial/pair
regressions, strict type checking of the two changed Python files, and Ruff style
and format checks. Commands, terminal outcomes, input hashes, and logs are retained
under `artifacts/jobs/lra-synthetic-spatial-eligibility/`.

This result supports spatial eligibility and regional country-neutral candidate
selection. Country-only map context and focal-country display counts require a
separate display consumer. It does not validate real source coordinates, source
admission, empirical ecological accuracy, or full numerical method parity.
