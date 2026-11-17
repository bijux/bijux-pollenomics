# BOKE/KRAG conditional nominal PPE comparison

Changing shared nominal Betula PPE from **5.106 to 4.94** increases outer-ring
adjusted Betula by **1.233837 percentage points** in this two-tree comparison.
Inner-ring signed Betula changes by **1.587917 points**, although clipping leaves
adjusted Betula at zero in both cases. Zero adjusted change therefore hides a
parameter effect; it is not evidence of vegetation absence.

The cases retain the same pooled 2700–3200 calendar-BP source support and physical
assumptions. Ulmus stays at 1.27 because the selected European reference has no
Ulmus RPP. Fall speeds and source SD metadata remain unchanged. The baseline keeps
its modeled 5.106; the separately reported author alpha 5.10571 is not substituted.
Both nominal cases use the declared Poaceae-reference scale, bound through retained
parameter correspondence and explicit reference RPP 1; scale correspondence alone
does not establish applicability or an uncertainty law.

This mixed-source sensitivity retains a **100 km** regional extent, while the
[2025 compilation's method](https://essd.copernicus.org/articles/17/2007/2025/)
describes **1000 km**. It does not reproduce that paper. The native 2025 `vg` field
is not admitted as fall speed or used here.

## Raw and adjusted results

Values are percentages; changes are comparison minus baseline in percentage
points. Regional source percentages are divided by 100 internally. Local adjusted
cover clips negative values and closes the surviving positive mass **within each
case before comparison**. Raw signed cover remains a separate estimand.

| Support | Taxon | Baseline raw (%) | Comparison raw (%) | Raw change (pp) | Adjusted change (pp) |
| --- | --- | ---: | ---: | ---: | ---: |
| Regional | Betula | 72.170000 | 72.829000 | 0.659000 | 0.659000 |
| Regional | Ulmus | 27.830000 | 27.171000 | -0.659000 | -0.659000 |
| Local midpoint 290.5 m | Betula | -15.419145 | -13.831227 | 1.587917 | 0.000000 |
| Local midpoint 290.5 m | Ulmus | 115.419145 | 113.831227 | -1.587917 | 0.000000 |
| Local midpoint 750 m | Betula | 17.979015 | 19.212853 | 1.233837 | 1.233837 |
| Local midpoint 750 m | Ulmus | 82.020985 | 80.787147 | -1.233837 | -1.233837 |

Inner-ring adjusted composition is exactly `[0, 1]` in both cases. Outer-ring
adjusted Betula rises from 17.979015% to 19.212853%. These are conditional model
outputs, not independent observations or evidence of improved ecological accuracy.
The clipping policy is the project assumption reported from discussion with
supervisor Anneli Poska (personal communication; date unrecorded), not a universal
claim about the source paper. Zero surviving positive mass would refuse a case.

## Support and uncertainty limits

Two cases share two taxa, one regional pooled-source bin, one local pooled-source
bin and two local rings: six coordinates per case. Selected modeled panel counts
are 542 regionally and 675 locally. These are not full native pollen NISP,
vegetation fractions or admitted terrestrial denominators. Full and excluded native
pollen denominators are not bound to these saved pooled-bin requests. The parent
pilot's separately audited 2,553 BOKE and 3,973 KRAG full-taxon totals remain
distinct; no allocation or excluded mass is inferred from them. Pooled-bin IDs
are not native dated samples.

The retained basin-diameter assumptions are 1674 m regionally and 160 m locally.
Local annuli are 81–500 m and 500–1000 m, with mean radii 290.5 m and 750 m.
Declared-bin stationarity, counts, taxon axes and configuration remain fixed.

This is **unweighted sensitivity**. It supplies no implicit probabilities, weighted
mean, covariance, source standard error or confidence interval. Count, chronology,
basin, source-SD and model uncertainty are not propagated. Full forest/open/cereal
cover, applicability, scientific input admission and measured vegetation accuracy
remain unestablished. The project's ten-percentage-point accuracy criterion cannot
be evaluated without a compatible independent reference.

## Saved result qualification

Two model cases and publication completed, but a late operator software audit
refused an opaque identity read. The original operator has no successful terminal
receipt. Its failure remains immutable; the saved result was independently
qualified without rerunning either model. The [separate verification](verification.json)
records numerical parity with the prior accepted comparison, clipping, exact
request/parameter lineage, source identity and their distinct review scopes.

The [saved report](result/report.json), [original numerical tables](result/README.md)
and [source-case manifest](result/source-cases/manifest.json) remain byte-identical
to that saved epoch. Original source members and full child bundles remain private.
The public projection grants neither their redistribution nor empirical source
accuracy. Future uncertainty or accuracy claims require separate prospective
source, design-law and independent-target qualification.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Two deterministic conditional Betula/Ulmus nominal cases retain pooled support and compare shared Betula PPE 5.106 versus 4.94 with fixed Ulmus 1.27, source SD metadata and fall speeds.

**Unsupported claim.** No full forest/open/cereal cover, binding of full/excluded native pollen denominators to these saved requests, empirical accuracy, source-SD probability law, scientific input admission or 2025 paper reproduction.

**Actual verification performed.** The maintained consumer produced two cases before a later software audit refused. Separate saved-output and request/parameter-lineage verification established numerical parity and unchanged support; this packet retains exact scopes and byte pins.

**Remaining input or review.** Independent applicability, terrestrial denominator, chronology allocation and empirical reference qualification remain open. A clean future operator needs a prospectively corrected identity bootstrap; no model rerun is needed to preserve this accepted saved result. Resolver: source-method maintainer Reopen when: A prospectively reviewed source applicability, denominator or independent-reference decision is available.

**Cause category.** Conditional nominal PPE sensitivity with separately qualified saved output after a refused terminal operator.

**Consequence.** Outer-ring adjusted Betula changes by +1.233837 percentage points; inner signed Betula changes by +1.587917 points while both adjusted values remain zero.

**Precise next acceptance route.** Use the pinned maintained consumer and explicit source-case contracts for future declared contrasts; separately qualify applicability, uncertainty laws and independent accuracy targets before claiming them.

**Negative or refused result.** The original operator has no successful terminal receipt: a late opaque software example identity read was guard-refused. That failure remains unchanged; output qualification is separate. Inner adjusted equality does not establish no parameter effect.

**Matched denominator.** Two cases, two taxa, one regional and one local pooled 2700–3200 calendar-BP bin, two local rings, six coordinates per case. Selected modeled panel counts 542 and 675 are not full native N; full/excluded denominators are not bound to these saved requests. Separately audited 2,553 BOKE and 3,973 KRAG full-taxon totals remain distinct without an inferred join or excluded mass. Retained 100 km regional extent differs from the 2025 paper's 1000 km.

Retained evidence: [reports/science/pollen-reconstruction/bokesjon-pilot/parameter-sensitivity/result/report.json](result/report.json), [reports/science/pollen-reconstruction/bokesjon-pilot/parameter-sensitivity/result/source-cases/manifest.json](result/source-cases/manifest.json), [reports/science/pollen-reconstruction/bokesjon-pilot/parameter-sensitivity/verification.json](verification.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
