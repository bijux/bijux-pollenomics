# Abborrtjärnen five-taxon reconstruction with unknown PPE dependence

The new [conditional profile](protocol.json) reconstructs one common five-taxon
composition at the ABBO core and asks how unknown correlations between shared
pollen productivity estimates (PPEs) affect uncertainty in temporal changes.
It uses the literal panel **Betula, Cyperaceae, Juniperus communis, Pinus
sylvestris and Poaceae** in four previously frozen native-BP windows. This
extends the earlier two-taxon conditional calculations to a different,
explicitly closed estimand; it does not reproduce LandClim or revise the
historical core-admission decision.

The [actual result](result.json) retains all 107 current native samples. Exactly
29 explicitly report all five panel taxa in the four windows; 78 lie outside
the requested windows. No selected sample is dropped for missing measurements,
and no absent taxon is filled with zero. The raw −52 BP age of sample 173173
remains outside these windows. The selected points contribute 28,016 panel
counts out of 34,085 reported pollen NISP, leaving **6,069 reported counts
outside the panel**. That larger sum includes source pollen categories beyond
the declared estimand; it is not an authenticated terrestrial denominator.

| Native-BP window | Samples | Panel counts | Reported pollen outside panel | Conditional Betula fraction | Conditional Pinus sylvestris fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1500–<2000 | 7 | 5,645 | 2,433 | 0.289858 | 0.542021 |
| 2000–<2500 | 9 | 8,056 | 2,051 | 0.391545 | 0.486622 |
| 2500–<3000 | 8 | 8,903 | 982 | 0.363269 | 0.546851 |
| 4500–<5000 | 5 | 5,412 | 603 | 0.385828 | 0.550473 |

The result contains all five fractions and full covariance matrices. Table
values are rounded for display. They describe composition within this panel,
not whole vegetation cover or an independent vegetation measurement.

Each window uses the maintained physical inverse and covariance API. The
receiver is a declared static circular disk derived from the source-reported
3 ha area, with radius `sqrt(30000/pi)` metres. A homogeneous terrestrial
annulus extends to 100 km; wind is 3 m/s, the empirical transport coefficient
is 0.12, and the turbulence parameter is 0.25. The transport convention is
stationary and isotropic, with uniform disk reception. It attributes all panel
pollen to land outside the receiver and supplies no lake-margin source term;
Cyperaceae and Poaceae can violate this assumption in actual basins. Neither
the circle nor its constant historical extent is a field finding.

The point ages come only from native chronology 11516. AD 1950 is a declared
reference interpretation, not a separately authenticated field in this
capture, and no CE conversion is performed. No age distribution, alternative
chronology, failed Bacon draw, fall-speed uncertainty or geometry uncertainty
enters the calculation. Within each window, pooled counts have a fixed-total
multinomial working law at the observed proportions, assuming one common
composition. Disjoint native sample identities permit independent window
count draws **under that declared law**; they do not demonstrate ecological
or temporal independence or account for overdispersion.

The five native names match the public parameter row labels literally.
Applying those parameters to these source concepts remains an explicit
transfer assumption. The deposited header says `PPE (SD)`; the primary
[Table 1 caption and Appendix B](https://essd.copernicus.org/articles/14/1581/2022/)
describe standard deviations. Section 2.3 inconsistently uses “standard error
(SD)”. We retain that discrepancy and use the bracketed values as marginal
SD inputs for this conditional delta calculation, without a SEM conversion
or an interpretation as ecological variation between sites. Poaceae has
PPE 1 and SD 0 because it is the fixed relative reference in this profile.

One PPE error vector is shared across all four windows. The baseline assumes
diagonal PPE covariance and zero count–PPE covariance. For every one of the
six window pairs and five taxa, the calculation additionally considers every
real PSD PPE covariance with those same marginal variances. For a saved
scalar PPE derivative `g`, let `a_i = abs(g_i) * SD_i`. The sharp PPE variance
range is

`[max(0, 2*max(a) - sum(a))^2, sum(a)^2]`.

The producer reuses the existing exact rational vector-length feasibility
routine, with exact Fractions of the saved binary64 derivative and SD inputs.
Independent count variance is then added. It retains the complete 20×20
baseline joint covariance and all **30 prespecified contrasts**, each defined
as older-window minus younger-window composition. Each scalar has its own
attaining covariance possibilities; their extrema need not be attainable
under one common covariance matrix. These are bounds on linearized variance,
not cover bounds, confidence intervals, a chronology posterior or calibrated
uncertainty coverage.

Unknown correlation has its largest total-SE range for the Betula contrast
between 1500–<2000 and 4500–<5000 BP. The conditional change is **0.09596948**
in panel-fraction units. The diagonal-PPE SE is **0.01007574**; allowing the
fixed-marginal PSD covariance class changes its SE range to
**0.00963796–0.01077603**. Counting variance remains present even where the
PPE component can cancel. Eleven of 30 PPE lower variance bounds are zero;
the other 19 remain positive. No covariance or interval was selected using
this result, and no statistical significance or field direction is asserted.

The counts come from the distinct current official Neotoma/EPD capture,
dataset DOI [10.21233/2vzb-bg61](https://doi.org/10.21233/2vzb-bg61), attributed
to Thomas Giesecke, EPD and Neotoma under the retained current CC BY 4.0
policies. The original investigation is Giesecke (2005),
[*Holocene forest development in the central Scandes Mountains, Sweden*](https://doi.org/10.1007/s00334-005-0070-2).
The parameter source is
[Fyfe et al., PANGAEA.937075](https://doi.org/10.1594/PANGAEA.937075), CC BY 4.0.
The older [PANGAEA.738429](https://doi.org/10.1594/PANGAEA.738429) profile is
CC BY-NC 3.0: only its descriptive header supplies the reported area fact;
its whole file is hashed, while its pollen measurements are not parsed or
redistributed. No broader licence or commercial-use authority is inferred.
The original April capture remains unchanged, and the current source match
does not recover historical wire custody. These windows and counts were
already exposed development material.

The committed producer ran at
`ccf316e22bec8d31fe589d2a7541e89cd6338eb5` in owned session 94916 and returned
native exit 0. The collection elapsed 1.574967750 seconds; `/usr/bin/time`
reported 1.53 seconds and peak RSS 142,049,280 bytes. The producer's own
scientific elapsed time was 0.429103125 seconds. It made five receiver-response
calls and 64 fixed-site covariance API calls, including a separate maximum
PSD covariance witness shared by both windows of each contrast. The
162,547-byte native JSON is copied here unchanged. The 60-second alarm,
512 MiB post-run RSS budget and 10 MB output budget were met; the RSS budget
was checked after execution and was not an in-process memory limit.

Twelve focused source/missingness/closure/dependence controls, configured
Ruff, formatting, strict types and protocol JSON parsing passed before the
source commit. The independent observer subsequently ran from committed
source `4c2188cf5ae25afeb5712d642b4fab5f128935a5` against this exact producer
result and returned exit 0 in 0.398165584 seconds, with peak RSS 49,250,304
bytes. It checked all 107 original sample accounts, the 29 selected samples,
four windows, five taxa, 30 contrasts and 400 joint covariance cells through
independent scalar/Fraction arithmetic. Its maximum scalar or covariance
residual was **1.4224732503009818e-16**, within the declared absolute 2e-14
plus relative 2e-12 tolerance. Saved transport factors were held fixed; this
does not claim a separate quadrature check of the five new response values.

Sixty independently constructed Gram covariance witnesses attain the lower
and upper scalar extrema, with maximum floating Gram variance residual
**3.3881317890172014e-21**. Each also admits a positive four-point PPE moment
witness at the published means and marginal SDs; the minimum support value
is **0.8912936765254621**. These 60 moment witnesses establish feasibility,
not an adopted probability law or one simultaneous extremal covariance.
The independent check confirms the 11 zero PPE lower bounds and adds no model
fit, ecological calibration or original-core admission. Its exact command,
source commits and terminal facts are retained in
`artifacts/physical-core/abborrtjarnen-ppe-dependence/independent-check/execution.json`;
the independent JSON is beside that record. The complete independent output
directory is 4,512 bytes.

From the repository root, replay the committed consumer against the qualified
original source store into an absent output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence \
  --repository "$PWD" \
  --source-root /path/to/qualified/source-store \
  --output "$PWD/artifacts/physical-core/abborrtjarnen-ppe-dependence/replay"
```

The actual bounded invocation, stdout, stderr and resource facts remain under
`artifacts/physical-core/abborrtjarnen-ppe-dependence/`. No model was fitted,
no measured vegetation target was opened, and no calibrated accuracy,
whole-vegetation, original-method or original-core-admission claim follows.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Conditional five-taxon physical reconstruction and exact sharp linearized PPE-variance bounds over all PSD covariances with the declared marginal SDs, sharing PPE across four windows and preserving all 30 scalar temporal contrasts.

**Unsupported claim.** One globally attaining covariance for all extrema, adopted four-point probability law, nonlinear cover/confidence bounds, empirical interval coverage, age uncertainty, whole vegetation, original LandClim reproduction or core admission.

**Actual verification performed.** Producer ccf316e22 made five receiver and 64 fixed-site covariance calls and exited zero. Independent scalar/Fraction checks compared 107 accounts, 29 selected samples, four windows, 30 contrasts and 400 joint cells, with maximum scalar/covariance gap 1.4224732503009818e-16. Sixty Gram extrema and positive four-point moment witnesses passed, minimum positive PPE support 0.8912936765254621. Twelve focused controls and configured lint/types passed; saved response factors were held fixed by the observer, not independently re-integrated.

**Remaining input or review.** The completed delta calculation holds native point ages, a static 3 ha receiver and literal five-taxon transfer fixed; unknown fixed-marginal PPE correlations are bounded mathematically but do not identify a joint ecological probability law, whole-vegetation denominator or field coverage. Resolver: Analyst declaring any different covariance/age/physical model; independent vegetation and palynological expertise only for a broader field interpretation or admission claim. Reopen when: A broader claim supplies source-bound physical/taxon support and independent vegetation/error evidence or a separately prespecified uncertainty law; it must not reinterpret the per-contrast extrema as one simultaneous distribution.

**Cause category.** assumption|comparability

**Consequence.** Use the reconstruction and dependence bounds only within the explicitly closed panel and fixed nuisance profile, with source SD/SEM wording and relative-reference limits visible.

**Precise next acceptance route.** Retain the completed mathematical bounds as scoped results. A new age, field or whole-vegetation question needs its own declared source support and estimand; do not promote moment feasibility to an adopted sampling law or require an umbrella approval to reuse the present conditional arithmetic.

**Negative or refused result.** No selected sample was dropped or absent taxon zero-filled. Eleven PPE lower variance bounds are zero and nineteen positive; each scalar extremum has its own witness, not one jointly attaining law. Original point-age/core decisions and omitted native pollen remain unchanged; no field significance or direction was accepted.

**Matched denominator.** 107 original sample accounts; 29 selected and 78 outside four frozen windows, with 7/9/8/5 members. Five literal taxa contribute 28,016 panel counts of 34,085 reported pollen NISP, leaving 6,069 reported counts outside the panel; 20 joint components and 30 prespecified contrasts.

Retained evidence: [reports/science/pollen-reconstruction/abborrtjarnen-ppe-dependence/result.json](result.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
