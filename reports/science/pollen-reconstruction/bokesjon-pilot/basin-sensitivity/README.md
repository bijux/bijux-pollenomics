# Bökesjön: conditional static-basin sensitivity

[Return to the pilot source assessment](../README.md).

**Three source-based modern basin profiles produce an outer-ring difference of
3.03 percentage points.** This is a development sensitivity result for a
Betula–Ulmus composition at 2700–3200 cal BP. It does not establish forest cover,
ancient lake geometry or vegetation accuracy.

| Static profile | Equivalent radius (m) | Inner signed Betula (%) | Inner clipped Betula (%) | Outer clipped Betula / Ulmus (%) |
| --- | ---: | ---: | ---: | ---: |
| Modern 1.5 ha | 69.10 | −6.95 | 0.00 | 21.01 / 78.99 |
| Modern 1.6 ha | 71.36 | −8.64 | 0.00 | 20.38 / 79.62 |
| Metadata 80 m | 80.00 | −15.42 | 0.00 | 17.98 / 82.02 |

The inner ring runs from one metre outside the assumed shoreline to 500 m;
the outer ring is 500–1000 m. The two fractions in each ring refer only to the
selected tree taxa. [All six rows, including signed Ulmus values](cover.csv)
and [full numerical products and source pins](result.json) retain precision.

Clipping sets negative signed fractions to zero and renormalizes the surviving
positive mass. It yields inner-ring Betula = 0 and Ulmus = 100% in all three
profiles, although the signed estimates differ by **8.47 percentage points**.
The resulting zero is a policy-transformed estimate, not evidence of absence.
Zero surviving mass would fail explicitly; no such refusal occurred here.

## What changed, and what was held fixed

The [basin source declaration](../../../../../data/neotoma/raw/bokesjon-core-sources/basin-sources.json)
retains the county report and SMHI catalogue's 1.5 ha, the published table's
1.6 ha, and the LandClim metadata's 80 m radius. These are separate modern
source profiles, not minimum/maximum ancient bounds or a probability interval.
The SMHI chart has neither a survey date nor a marked pollen-core station.

Each profile used a fresh public-host LRA request and freshly generated kernels.
Changing radius changes both the receiving basin and the inner ring's edge and
area. This is therefore a joint declared-geometry sensitivity, rather than an
isolated basin parameter experiment or an observed relevant source area of pollen.

The existing two-taxon parameter profile, neutral transport with 3 m/s wind,
KRAG regional basin radius 837 m and regional extent 100 km, homogeneous
terrestrial rings and source chronology/count selection were held fixed.
The selected public counts independently rejoin the pooled requests:
BOKE Betula/Ulmus = 570/105 from three samples and KRAG = 506/36 from four.
The legacy pooled evidence does not enumerate its original sample owners;
this check establishes aggregate/window/entity agreement, not a recovered
historical per-owner custody ledger.

The 80 m replay matches the saved baseline exactly. The maximum outer-ring
pairwise span is 3.0307543271 percentage points; the maximum signed inner span
is 8.4705726064 points. The user's 10-point guidance is shown only as a
**sensitivity marker**. No independently measured cover is available to score
absolute cover error or scientific acceptance.

## Execution and independent readback

The producer ran at source `27aa710e39cc1ba3667c363eeac5f1ed97e758bc`, after the
source audit at `916c9489de8fd4fcac24fcf973add288f7ea2c86`. All three requests
completed: **4.90 s, 202,637,312 bytes peak RSS and 198,024 product bytes**.
The 180-second timeout was enforced; 512 MiB RSS and 16 MiB output bounds were
measured after completion. [Execution receipt](execution.json).

The independent observer authenticated all 12 consumed pins and the earlier
35 source-audit pins, all three requests and generated products. It independently
checked geometry, inverse LOVE, nonnegative closure, pairwise spans and the exact
baseline. Maximum scalar discrepancy was 5.33e−15; the area arithmetic discrepancy
was 3.82e−6 m². It reused the unchanged qualified transport implementation and
did not independently repeat transport quadrature. [Independent proof](independent-check.json).

An initial observer stopped on a raw-evidence interface mismatch. That stopped
attempt and an intermediate successful check are retained alongside the final
observer and proof; neither was a scientific producer failure. The final proof
identifies its executed observer by SHA-256. Software verification covers
**93 focused pilot tests**, including the source suite and 26 basin tests.

Reproduce from a checkout of the calculation commit, with the exact declared
inputs available and the host, LRA and development packages installed:

```bash
python -B -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity.workflow \
  --repository . --output artifacts/bokesjon-basin-reproduction \
  --source-sha 27aa710e39cc1ba3667c363eeac5f1ed97e758bc
```

The consumer requires an absent output directory and the specified committed
source; a later documentation commit does not change the calculation identity.
Scientific admission still requires justified taxon/PPE/chronology, static-basin
and regional-background choices. Modern-size agreement cannot supply those decisions.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Three declared static-basin profiles have a maximum 3.03-percentage-point outer-ring difference in a two-tree composition; clipping masks an 8.47-point signed inner-ring difference.

**Unsupported claim.** Measured vegetation accuracy, total forest/open/cereal cover, an observed ancient shoreline, calibrated geometry uncertainty or scientifically accepted BOKE/KRAG inputs.

**Actual verification performed.** Three fresh host requests; 93 focused pilot tests; independent authentication of 12 consumed and 35 prior pins, source-count aggregate joins, numerical inverse/closure and exact 80 m baseline; maximum scalar error 5.33e-15. Transport quadrature was not independently repeated.

**Remaining input or review.** Justified physical, taxon/denominator/PPE and chronology decisions, with compatible independent measured cover. Resolver: qualified BOKE/KRAG source and scientific reviewers and a vegetation-reference owner. Reopen when: Scoped source decisions or a compatible measured-reference packet is available.

**Cause category.** assumption|comparability|data|qualified review

**Consequence.** Retain signed diagnostics beside clipped results; do not turn the 10-point sensitivity marker into an accuracy verdict.

**Precise next acceptance route.** Obtain scoped source/profile decisions and execute supported categories, then evaluate a separately frozen compatible independent reference.

**Negative or refused result.** All three inner-ring signed Betula estimates are negative and become zero after clipping; no zero-surviving-mass refusal occurred. No measured accuracy score is available.

**Matched denominator.** Three profiles, two rings and two taxa; three BOKE and four KRAG sample owners in one exposed 2700–3200 cal BP development window.

Retained evidence: [result](result.json), [cover table](cover.csv), [independent proof](independent-check.json), [execution receipt](execution.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.
<!-- scientific-verification-and-limits:end -->
