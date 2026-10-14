# Bökesjön basin source review

The [1985 Skåne lake-sediment report](https://www.lansstyrelsen.se/skane/om-oss/vara-tjanster/publikationer/1985/de-sydvastskanska-sjoarna.-sedimentens-sammansattning-och-funktion..html)
lists Bökesjön as a small lake. Its Table 3 (printed page 35, PDF page 42)
reports a surface area of **0.015 km² = 1.5 ha**, mean depth 3.0 m and maximum
depth 4.8 m. Figure 22 (printed page 40, PDF page 47) maps the depth contours
from a winter 1984 survey and marks a sediment sampling point `A`. The report
does not identify `A` as the later Neotoma/EPD pollen core or provide a
time-varying lake boundary. The downloaded source PDF was inspected outside
the repository and has SHA-256
`2b34d1794a1b1d8d14318db49519c879da8ee934d35645a63035fa4e08db6e93`.

An independent [lake sampling table](https://academic.oup.com/view-large/80999410)
reports Bokesjön at 55°34′31.6″ N, 13°26′15.7″ E with area **0.016 km² =
1.6 ha**. Its coordinates convert to 55.57544444° N, 13.43769444° E, about
**17.7 m** from the Neotoma site 28872 coordinates (55.57556° N, 13.4375° E).
This supports the same-lake lead. It does not identify the sampled water with
the pollen core, or bind the area to a fossil-pollen age.

The [LandClim II site metadata](https://doi.org/10.1594/PANGAEA.937075)
(`LandClimII metadata.xlsx`, `LANDCLIMII metadata file`, row 977) gives `BOKE`,
site type `lake`, `siteradius` **80** and site coordinates 55.575556° N,
13.4375° E. The governed local workbook bytes have SHA-256
`2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb`.
If 80 represents a circular radius in meters, its area is **2.0106 ha**,
larger than either reported modern lake area. This comparison does not prove
which radius or outline LandClim used at each modeled age. The historical
basin geometry, workbook-to-Neotoma core identity and LRA radius remain
**unadmitted**. The observed-pollen holdout does not depend on them.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** Two modern Bökesjön area sources and nearby points provide a same-lake lead with an explicit circular-radius comparison.

**Unsupported claim.** Neither the 1984 sediment station A nor a modern lake point identifies the pollen core or its age-specific basin.

**Actual verification performed.** Read the source-specific area/coordinate review and bound Swedish core-comparison report; no PDF recapture, polygon digitization or new geometry calculation.

**Remaining input or review.** Original pollen-core identity, source-area temporal meaning and a justified sample-age basin model remain required.

**Cause category.** Modern geometry evidence lacks temporal and physical-core authority.

**Consequence.** The 80 m LandClim radius is not transferred; 1.5 ha, 1.6 ha and 2.0106 ha circle values remain distinct source/scenario quantities.

**Precise next acceptance route.** Link the physical pollen core to dated geometry or justify an explicit alternative static basin profile with permitted use and sensitivity.

**Negative or refused result.** Historical basin geometry and every Bökesjön LRA input remain unadmitted.

**Matched denominator.** 1 named lake lead; 2 reported modern areas; 1 published 80 m radius comparison; 0 reconstructed ages or admitted basin samples.

Qualified authored reader SHA-256: `5f98f626009b775982e548996a63135c3c6553f6f2afd9b8c2eb82f9fa7a891f`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-lake-core-identity/report.json](../swedish-lake-core-identity/report.json) (SHA-256 `d2b80a81ed26c7d3f327488290927de6220a3ca39c8d7d15514c258c75dc7594`).

- [Retained qualification evidence: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md) (SHA-256 `264420c81e18a6ee56b0b612e657f881fa26829a9cc060114d69b15d2491120f`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
