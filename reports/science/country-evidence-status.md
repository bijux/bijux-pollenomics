# Scientific evidence by Nordic country

The original 31-target four-country result asks whether observed pollen composition transfers to a country excluded from training. It predicts the **31 non-excluded targets** in the LandClim II author taxonomy lookup, using selected Neotoma/EPD pollen counts in **500-cal-BP site-bins**. Three fixed baselines predict each eligible bin; a bin without the required training-site support is refused. The [machine-readable matrix](country-evidence-status.csv) retains the native pollen count mass, assigned mass, excluded and unmapped mass, attempted and scored bins, and exact result paths. These are previously exposed **development** cohorts, not untouched confirmation, REVEALS/LOVE reconstructions or measured vegetation tests. The [cohort account](source-cohorts.md) and separate [Denmark/Finland/Norway](denmark-finland-norway-author-pollen.md) and [Sweden](sweden-author-pollen.md) accounts explain the selection and scoring rules.

| Held-out country | Physical sites; samples | Assigned / native pollen grains | Scored / attempted bins; refused | What this result can say |
| --- | ---: | ---: | ---: | --- |
| Denmark | 1; 91 | 122,998 / 129,768 | 24 / 24; 0 | One-lake pollen transfer only; no between-site Danish skill estimate. |
| Finland | 28; 1,797 | 1,229,019 / 1,260,281 | 435 / 435; 0 | Pollen transfer on the selected Finnish sites and bins. |
| Norway | 52; 3,544 | 2,018,295 / 2,286,020 | 1,084 / 1,178; 94 | Pollen transfer on supported bins; 94 bins lacked two eligible positive-target training-site groups and were refused, not scored as zero. |
| Sweden | 3; 228 | 221,800 / 240,966 | 51 / 54; 3 | Three Swedish lakes held out together; three bins lacked foreign training support. |

Across these declared populations, **1,594 of 1,691 attempted site-bins** were scored, **97** refused, and the scored bins yield **4,782 method rows** across three fixed methods. These sums describe a shared 31-target response, not a pooled four-country accuracy estimate. Counts outside the 31 targets remain visible in the [taxonomy ledger](../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv) and the [Swedish result](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json). The earlier **16-label** analysis has another response denominator; its scores cannot be compared numerically as if the axes were identical. Country exclusion and frozen predictions support this bounded development comparison, while earlier exposure of the Nordic outcomes prevents an independent confirmation claim.

## Separate conditional physical-forward evidence

The [matched physical-forward study](pollen-reconstruction/matched-pollen-forward/README.md)
adds a conditional numerical result without changing any population or source
admission in the original 31-target country comparison above. Its saved
metadata geometry and explicit two-taxon projections are not historical basin
qualification or independent vegetation. The machine-readable country matrix
keeps every original field and appends separately named conditional fields.

| Country | Retained source cores / places | Target cores / windows in this consumer | Physical-forward evidence role |
| --- | ---: | ---: | --- |
| Sweden | 4 / 4 | 4 / 77 | Two scopes give 154 contexts and two families give 308 outcomes: 200 scored and 108 refused. Only BOKE/BUS have four-way matched support: 26 windows at two physical sites. |
| Denmark | 2 / 1 | 0 / 0 | SOLSOE81 and SOLSOE83 are distinct cores at one place. SOLSOE83 is the only added source on 12 jointly matched pooled contexts; there is no Danish target score. |
| Finland | 1 / 1 | 0 / 0 | Laihalampi is present and supplies other Swedish pooled contexts. Its axis does not support the jointly matched BOKE/BUS panel; no Finnish target was requested. |
| Norway | 1 / 1 | 0 / 0 | Dalmutladdo is present and supplies other Swedish pooled contexts. Its axis does not support the jointly matched BOKE/BUS panel; no Norwegian target was requested. |

These zero target counts describe this particular consumer, not missing
national pollen, a biological absence or failed source access. The pooled
physical mean MAE/TV on the 26 joint windows is 0.108040 versus 0.120778 for
the same-source direct baseline, but BUS is poorer (0.154732 versus 0.154539).
All 108 refused family outcomes remain explicit. An independent 50-digit
Decimal calculation matched 1,424 values at the frozen 1e-12 tolerance.
Previously exposed point-pollen agreement supplies no four-country accuracy,
independent measured vegetation, calibrated uncertainty or qualified
historical/field source admission. The missing source and review gates below
therefore remain open.

| Evidence needed for a stronger country claim | Current disposition and source route |
| --- | --- |
| A named REVEALS/LOVE input | **Zero samples admitted to LRA in these studies.** The [LRA source decisions](source-cohorts.md#lra-source-gate) require one physical core and time window with selected ages, historical basin geometry, eligible counts and taxon denominator, PPE/fall speeds, and permitted use. Danish **Solsø** still lacks the actual 79 historical input rows, selected chronology and dated basin ([decision](solsoe-lra-input.md)); Finnish **Laihalampi** has a 150-sample single-core lead but no selected age vector or dated basin ([decision](laihalampi-lra-input/README.md)); Norwegian **Dalmutladdo** has 72 matched samples and 11 matched radiocarbon controls, while historical basin and printed-interval dispositions remain open ([decision](dalmutladdo-lra-input/README.md)); Swedish **ABB/ABBO, BUS and BOKE** have site or depth correspondences without qualified same-window age, basin, denominator and parameter packets ([Swedish source questions](../../docs/report/pollen-reconstruction/swedish-source-questions.csv)). This is an admission refusal for these cohorts, not a finding that the LRA engine cannot operate. |
| Original historical-paper correspondence | The later author example can be executed and compared numerically, but **zero of 1,128 publication sequence records** are authenticated as original primary inputs or reproduction-ready rows. The exact historical site/window membership, transformations, PFT classification and grouped uncertainty remain open, so a full original-paper replay is unavailable ([publication correspondence](publication-correspondence.md)). The country pollen scores above do not resolve that archive provenance. |
| Independent measured vegetation accuracy | **Zero admitted Nordic measured pollen–vegetation pairs** among 16 nearby EMPD2–NFI candidates; no repository vegetation accuracy score was calculated. A historical map, modeled LandClim grid or published figure is not an independent matched outcome for these country predictions ([vegetation decision](vegetation-reference.md)). |
| HYDE and other context | Each country has **21 retained HYDE modeled cropland totals**, seven CE labels by three scenarios, or **84** across four countries. The exact retained release/version, native-grid CRS/calendar/estimand and use terms remain under [source review](hyde-cropland-source-account.md); these are modeled context, not pollen or measured-cover truth. [SEAD chronology rows](source-cohorts.md#context-and-validation-sources) have zero admitted ecological events; Sweden-only RAÄ authority is refused for analytical density. No archaeology count enters this pollen study. A later four-country archaeology comparison would require appropriate national sources and comparable units, coverage, rights and time support. Missing national capture is unknown, not zero. |
| Country boundaries and source authority | The pinned Natural Earth point assignments are computational evidence, while the [named-island and near-border queue](../../data/boundaries/review/review_queue.json) retains **147 flagged point decisions** and four country-boundary suitability items pending qualified review. The review question also separates six Neotoma retained-only site/dataset pairs from present selector decisions. AADR country-product rows and animal map labels remain context, not scientifically admitted country observations ([cohort account](source-cohorts.md#context-and-validation-sources)). No cross-border ecological conclusion is promoted from a coordinate alone. |

No qualified scientific decisions have been received for these country claims; source checks and model scores do not establish approval. The next acceptance route is a versioned, use-permitted packet for one named core or reference pair, followed by the corresponding source consumer and an independent decision scoped to that claim. This page reconciles retained reports and machine rows; it records no new scientific run or reviewer judgment.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Four-country 31-target development populations, count mass, score/refusal support and distinct source/review gaps are reconciled from retained machine rows. Separate conditional physical-forward source/target roles and all score/refusal denominators are explicit per country without changing the original 31-target populations.

**Unsupported claim.** Accepted Nordic LRA reconstruction, independent vegetation accuracy, full original paper replay, untouched confirmation or four-country scientific release approval.

**Actual verification performed.** Read-only result/coverage/taxonomy reconciliation, 21 HYDE rows per country, 36 unreceived review questions, 147 flagged boundary decisions and local links; no scientific study rerun. The distinct conditional physical-forward producer completed at a890b5e433fd2679768b588bae2774aa3d382e17 with native/collector exit zero and all 6,668 pins unchanged. Its independent Decimal50 check matched 1,424 values at absolute tolerance 1e-12, maximum residual 1.9653480873864026090362878350698437E-16. These saved results are synthesized without repeating prediction or scoring.

**Remaining input or review.** The original prior-exposed direct-pollen country results and new conditional Swedish physical-forward point comparison do not supply historically qualified basin/core packets, authenticated original-paper inputs, independent measured vegetation or qualified country scientific approval. Resolver: Named core and reference custodians; independent chronology, basin, boundary and scientific reviewers Reopen when: A versioned same-core/window packet, independent measured reference or qualified decision changes one country claim; replay only that affected consumer.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Country display and direct-pollen transfer remain development/context evidence with separate input, vegetation and scientific acceptance gates.

**Precise next acceptance route.** Bind one named core or independent reference to lawful source bytes and the full age/basin/count/parameter support; obtain an independent scoped decision, then consume only its accepted fields.

**Negative or refused result.** 94 Norwegian and 3 Swedish bins refused; zero LRA samples admitted through the original 31-target studies, zero admitted Nordic measured-cover pairs and zero received qualified decisions. The conditional physical-forward comparison retains 108 no-eligible-source family refusals; pooled BUS MAE/TV is poorer than direct (0.154732 versus 0.154539).

**Matched denominator.** 84 selected sites; 5,660 samples; 31 author targets; 1,594/1,691 scored/attempted bins; 97 refused; 4,782 method rows across three fixed methods. Separate conditional physical-forward support: eight source cores/seven places, four Swedish targets/77 windows, 154 contexts/308 family outcomes, 200 scored/108 refused; only 26 jointly matched windows at BOKE/BUS, 13 each, enter the two-target comparison. All scored panels have two taxa. SOLSOE83 adds source support on 12 joint pooled contexts; no DK/FI/NO target score.

Retained evidence: [reports/science/country-evidence-status.csv](country-evidence-status.csv), [docs/report/regions/nordic/author-target-pollen/report.json](../../docs/report/regions/nordic/author-target-pollen/report.json), [docs/report/regions/nordic/swedish-author-target-pollen/report.json](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json), [docs/report/validation/empd2-nfi-pairing/report.json](../../docs/report/validation/empd2-nfi-pairing/report.json), [data/boundaries/review/review_queue.json](../../data/boundaries/review/review_queue.json), [reports/science/pollen-reconstruction/matched-pollen-forward/README.md](pollen-reconstruction/matched-pollen-forward/README.md), [reports/science/pollen-reconstruction/matched-pollen-forward/report.json](pollen-reconstruction/matched-pollen-forward/report.json), [reports/science/pollen-reconstruction/matched-pollen-forward/decimal-comparison.json](pollen-reconstruction/matched-pollen-forward/decimal-comparison.json), [reports/science/pollen-reconstruction/matched-pollen-forward/publication.json](pollen-reconstruction/matched-pollen-forward/publication.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
