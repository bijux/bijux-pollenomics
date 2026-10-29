# Original Solsø core and basin evidence

The full [Odgaard (1994) published study](https://pure.au.dk/portal/en/publications/the-holocene-vegetation-history-of-northern-west-jutland/)
was inspected as the [Aarhus University PDF](https://pure.au.dk/ws/files/39023242/Odgaard_1994_combined.pdf)
(12,519,377 bytes; SHA-256
`f6959549f955a5bf17540f41ca6c295f11f584c88e550627718fc555a9c3dadd`).
The source PDF is retained in the private external source store at
`landclim/solsoe/odgaard-1994.pdf`, not republished here. The
[source-bound comparison](report.json) has SHA-256
`8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6`.

Figure 30 and its text (printed pages 35–36; PDF pages 32–33) map a Solsø
basin reconstruction for **9000 BC** from 51 corings. They mark the 1981 and
1983 cores at local coordinates (−33 m east, 64 m north) and (−50 m east,
70 m north), about **18.03 m apart**. The local figure has no georeferenced
origin. The paper says a 1.5 m fall in water level from 41.30 to 39.80 m
above sea level would halve the reconstructed lake area and volume. At the
1981/1983 corings it reports a water level of 40.80 m and only about
40 × 30 m of open water (printed page 34; PDF page 31). These are distinct
time and water-level claims; neither supplies a universal 89 m radius for
all pollen samples.

The paper explicitly uses the **1981 core** for 9700–5260 BC and 1540 BC–AD
1981, and the **1983 core** for 5230–1750 BC (printed page 42; PDF page 39).
It explains that a 1981 hiatus near 480–470 cm requires the 1983 core to
complete the Holocene record. Its seven 1983 radiocarbon controls in Table 17
(printed page 45; PDF page 42) match **all seven** distinct Neotoma controls
exactly by laboratory identifier, depth, radiocarbon age, one-sigma error and
δ¹³C. Neotoma represents each control in two chronology views, yielding 14
rows. This is an independent primary-source match for the 1983 core lineage.

The retained v1 report uses the historical half-unbounded 1981 predicate
`age >= 7210 OR age <= 3490`, together with 1983's 3700–7180 BP central-age
window. That conditional calculation gives 76 point proxies (56+20), or 74
within LandClim II's 10–11659 BP span. It omitted 1981's declared 9700 BC older
endpoint and AD 1981 surface endpoint and therefore is not the complete stated
paper-interval selection. The retained report and its 8456bf source epoch are
preserved rather than silently relabelled.

The corrected standalone source uses inclusive 1981 [-31,3490] and [7210,11650]
and 1983 [3700,7180] BP under the explicitly declared `BC + 1950` convention.
The 9700 BC paper endpoint is extrapolated; the convention does not resolve
no-year-zero calendar conversion or make the paper chronology equivalent to
Neotoma calibration. Its complete central-point selection total remains
pending a genuine registered replay. The revised producer is configured to emit a 92-row raw source
ledger, including uncertainty support, source comparability/refusal and native
locators, alongside descriptive proxy flags.

Point membership is not full-support containment or overlap. Native 353061
has a 12417 BP center outside despite overlapping 11495–13410 BP support;
353060's 11507 BP center is inside despite its 12037 BP older bound outside.
Native 352996's 7 BP center is inside but retains `refused`/`negative_bp`, raw
younger −41 and normalized endpoints null. Its proxy membership supplies no
analytical admission. Original 79 membership, chronology equivalence, original
provider history, dated georeferenced basin, rights and human scientific
acceptance remain unresolved. Zero Solsø LRA samples are admitted.

Replay against the retained Neotoma relations and private source PDF:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py \
  --repository . --paper /path/to/landclim/solsoe/odgaard-1994.pdf \
  --output artifacts/jobs/solsoe-original-study/replay
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

**Supported claim.** The retained original-paper comparison matches all seven distinct 1983 radiocarbon controls and describes explicit 1981/1983 core intervals and a 9000BC basin figure.

**Unsupported claim.** An ungeoreferenced 9000BC reconstruction and conditional calendar conversion cannot identify the 79 author input samples or provide one radius valid for every sample age.

**Actual verification performed.** Read the retained historical v1 account and source-bound closed central-point predicate controls. The older 76/74 comparison omitted two stated outer endpoints; no corrected source replay or fresh PDF table extraction was performed in this reading qualification.

**Remaining input or review.** The original author sample IDs, historical chronology and georeferenced time-specific basin outline remain missing for LRA.

**Cause category.** Historical core lineage established in part; author selection and physical basin support unresolved.

**Consequence.** Seven declared date matches support the documented 1983 core lineage. Historical half-unbounded 76/74 proxies remain distinct from complete closed central-point membership, uncertainty support, source eligibility and the published 79 author rows.

**Precise next acceptance route.** Run the corrected maintained source under a registered isolated stdlib profile, preserve all 92 raw source rows/refusals and independently verify native central-point inclusion/exclusion before reporting its total. Original 79 membership, chronology and dated basin/rights review remain separate.

**Negative or refused result.** Historical 76/74 proxies are not the complete paper intervals and do not recover79 author samples. Native352996 remains refused/negative_bp even if its central point is inside. LRA-admitted 0.

**Matched denominator.** Seven declared radiocarbon controls occur in 14 chronology-view relation rows; 92 raw central-age source records. Historical half-unbounded selection 76 (56+20), bounded 74; corrected complete-interval total is pending registered replay. One 9000 BC basin figure from 51 corings is not age-specific sample support.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json](report.json) (SHA-256 `8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
