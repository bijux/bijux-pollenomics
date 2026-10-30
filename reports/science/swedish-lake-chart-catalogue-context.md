# Archival lake-chart context for the Swedish field leads

SMHI's *Svenskt Vattenarkiv: Sjökartor och sjöuppgifter, Register 1987*
provides five separate chart entries for three of the four identified lake
leads in the existing field dossier. The
[typed source record](swedish-lake-chart-catalogue-context/source-records.json)
preserves their literal values, blank cells and shared provenance. The
[official publication](https://www.smhi.se/download/18.18f5a56618fc9f08e832bab2/1717803129630/Hydrologi_15%20Sj%C3%B6karte-%20och%20sj%C3%B6uppgifter.%20Register%201987..pdf)
is SMHI Hydrologi 15, by Torbjörn Lindkvist and Håkan Danielsson, © SMHI 1987.
These are archival catalogue facts, without a selected preferred chart,
current bathymetry claim or coring recommendation.

| Predeclared lead | Retained identifier | Catalogue disposition |
| --- | --- | --- |
| Finjasjön | 622731-136920 | Exact printed number `622731 136920`; one chart row |
| Östra Ringsjön | 619626-135565 | Exact printed number `619626 135565`; two chart rows |
| Havgårdssjön | 615365-134524 | Exact printed number `615365 134524`; two chart rows |
| Bjäresjösjön | 614958-137018 | Exact number not found in the available catalogue text; no absence claim |
| Uppåkra/Lund | Unresolved | No unique lake identifier; no substitute lake or parcel inferred |

The lookup used exact lake numbers, without a nearby-name or alias
substitution. The three positive matches were then compared directly with
their source page images. The negative text result for Bjäresjösjön is
limited by the catalogue's OCR-bearing text and is not exhaustive visual
proof that an entry, chart or lake is absent. All five original leads remain
represented; none gains a field decision from this lookup.

| Printed lake name | Chart | Drawing year | Scale | Area, km² | Volume, printed header `Mm³` | Maximum depth, m | Mean depth, m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Finjasjön | 3-0818 | Blank | 1:20000 | Blank | Blank | 13.2 | Blank |
| Havgårdssjön | 2-0170 | Blank | 1:4000 | Blank | Blank | 5.8 | Blank |
| Havgårdssjön | 3-1984 | 1983 | 1:10000 | 0.540 | 1.670 | 5.0 | 3.1 |
| Östra ringsjön | 3-2176 | 1982 | Blank | 20.220 | 1.247 | 16.4 | 6.2 |
| Östra ringsjön | 3-2177 | 1982 | Blank | 4.250 | 0.136 | 17.5 | 3.2 |

Finjasjön appears in section **88 HELGE Å**, printed page **84** (PDF page
86, zero-based index 85). Havgårdssjön appears in section **90 SEGE Å**,
printed page **85** (PDF page 87, index 86); the Östra Ringsjön entries are
on printed page **86** (PDF page 88, index 87). Multiple chart rows are
source evidence, not independent measurements of one common quantity. We
retain their different depths without averaging, choosing a row or guessing
whether they cover the same extent or reference water level. That catalogue
lookup did not acquire the actual charts or bathymetric grids. Subsequently
received Finjasjön, Havgårdssjön and Östra Ringsjön chart scans are described
separately below; the remaining lead dispositions are unchanged.

There is a concrete source arithmetic limitation. Interpreting the printed
volume header `Mm³` conditionally as million cubic metres, and km² as
million square metres, gives a volume/area ratio in metres. For Havgårdssjön
chart 3-1984, the exact ratio is **167/54**, approximately **3.09259 m**,
which rounds to the printed mean depth **3.1 m**. Under the same interpretation,
Östra Ringsjön chart 3-2176 gives **1247/20220**, approximately **0.06167 m**,
against the printed **6.2 m**; chart 3-2177 gives **4/125 = 0.032 m** against
**3.2 m**. The source images confirm that the volumes are visibly printed
as **1.247** and **0.136**. We have not repaired them as OCR errors, multiplied
them by 100 or substituted derived values. Coupled quantitative use of
volume, area and mean depth remains **unqualified**: the subsequently received
Ringsjön charts supply dated depth context but no volume, area or mean-depth
table that resolves these catalogue values. Reference levels and source meaning
still require qualification. Rounding agreement in the
Havgårdssjön control does not establish contemporary measurement accuracy.

The definitions on printed page **26** (PDF page 28, index 27) describe
charts held at SMHI in spring 1987. Their year column is the year a chart
was drawn, rather than the survey year. Neither publication year 1987 nor
the PDF server's `Last-Modified: 7 June 2024` is substituted for a blank
chart-drawing year or a measurement date. The catalogue defines lake numbers
using outlet X/Y in *rikets system*, with six digits and 10 m resolution.
We infer no EPSG code, lake-centre location or sampling coordinate from them.

The report cautions that lake quantities depend on water level and gives
a general estimated table error of about ±10%. That comment is not a
lake-specific error estimate, standard deviation or probability law. No
numeric confidence interval is constructed from it. All ten blank cells
remain null; they are neither zero measurements nor quantities derived
from another cell. Measurement dates and lake-specific reference water
levels remain unreported by those catalogue rows. The subsequently received
Finjasjön survey sheet and Ringsjön survey captions do not fill their blank cells.

The retained publisher PDF contains **4,226,310 bytes**, SHA-256
`b29f4ca2a847a4dc785d3738603e46817aa130c55c061b2d614d48857edc1fd3`,
under `hydrology/smhi/hydrologi-15-register-1987/` in the existing source store.
The original GET returned HTTP 200 and retained the declared content length,
but its downloader exited **1** after attempting to set a timeout through an
already closed response. Its original `body_complete=false` and literal
error remain unchanged. A separate offline check confirms the retained byte
length and hash, PDF header and final EOF marker; `pdfinfo` exited zero and
reported 180 pages. There was no second GET. Direct comparisons of rendered
PDF indexes **2, 27, 85, 86 and 87** confirm publication identity, definitions,
all five chart rows and the blank cells. This offline source qualification
does not relabel the failed acquisition process as successful.

Only factual transcription and the explicit conditional arithmetic check
are published here. The PDF and page images stay in their existing
source/artifact locations; no chart, grid or geometry is redistributed.
No report-specific open licence or geometry permission is inferred from
public access. The earlier
[Finjasjön record-route attempt](https://vattenwebb.smhi.se/svarwebb/?sjoid=622731-136920)
did not expose readable attributes in the available text reader. The
received screenshot below adds visible record context without relabelling
that attempt or authenticating a backend version. Individual-record routes
for the other leads were not queried; no undocumented API was used.

The subsequently received `622731-136920-kartor.zip` contains three scanned
TIFFs: `3-0818_Finjasjön_622731-136920.tif` and the `3-5807a`/`3-5807b`
Finjasjön files. The ZIP contains **502,622 bytes**, SHA-256
`cfcb528691d48ea713c697cdbdec78b4508a8c64d428da8794075dd7e6542396`.
The adjacent source record binds each member's bytes, hash and dimensions.
These are single-page, 1-bit scans with 600 dpi image resolution, without
embedded GeoTIFF positioning or a numeric depth grid. Their software and
ZIP timestamps do not establish map dates. The originals remain in place;
only local image derivatives were made for direct source comparison.

The `3-5807b` description sheet names Finjasjön, SMHI number `622731 136920`,
and records **performed year 1986**, **Gatukontoret**, **Hässleholms kommun**.
It states water level at measurement **0.2 m below normal mean water level**.
Sounding method and number of tracks/soundings are both `?`. Its scale token
`17096` agrees with the companion `3-5807a` chart's handwritten **1:17096**
and graphic 0–1000 m scale. That chart prints highest high, mean and lowest
low water surfaces **+45.20**, **+43.00** and **+42.30**; a named vertical
datum is not supplied. A faint handwritten annotation remains unresolved.
The separate `3-0818` scan contains Finjasjön contours, soundings and a
graphic scale. Its received filename and registry reference match the
catalogue chart identifier, but no survey date or named datum is established
from the scan. The catalogue's **1:20000**, **13.2 m** and blank drawing year
remain catalogue facts; 1986 and the 5807 water levels are not transferred
to 0818.

The supplied screenshot shows the public
[SMHI registry interface](https://vattenwebb.smhi.se/svarwebb/), Finjasjön
`622731-136920`, waterbody `SE622731-136920`, district `SE4`, the same three
chart references, and **Hässleholm Municipality** beneath the 5807 group.
It displays area **10.5085 km²**, maximum depth **13.2** with no adjacent unit,
and water-surface height **42 m**. English browser translation is active:
the version value literally reads **`ANSWER2016_3`**, which is not promoted
to an authenticated untranslated `SVAR2016_3` field. The screenshot is
**3,933,963 bytes**, SHA-256
`398e67cd83780ea6e2f71d6463325fdd7d4726e80086101b539dd4e2f65de495`.
It supports received download context, without a wire-captured download URL,
provider checksum, measurement epoch or licence. Its 42 m and the chart's
+43.00 mean level remain separate observations with unresolved datum and
date, without a corrected or preferred quantity.

The 5807a scan labels **RISKOMRÅDE VID SKJUTNING** and **Militärt
övningsområde**; 0818 labels **AVSTÄNGT VID SKJUTNING**. These are historical
chart annotations, without a claim about current restrictions, extents,
safety advice or permission. Direct full-chart, legend and scale comparisons
qualify this factual transcription only. No chart is selected, averaged,
digitized or georeferenced, and no basin, core join or field admission follows.

The received Havgårdssjön ZIP `615365-134524-kartor.zip` has **620,531 bytes**,
SHA-256 `242e5ae3f35708ba076d2c4aa65b067aa857be276a745eae4cf5096f08fbfcb1`,
and contains two single-page scanned TIFF charts.
Both have 1-bit image data and 600 dpi image resolution, without embedded
GeoTIFF positioning or a numeric depth grid. The handwritten `2-0170` scan
is titled **Karta öfver Hafgårds-sjön**, has individual soundings, a graphic
metre bar and archive number **2-170**. Its faint scale annotation is not
confidently transcribed: **1:4000** remains a separate catalogue value.
Neither survey date nor reference water level is established from this scan.

The `3-1984` sheet combines a contour map with a form naming lake number
**615365 134524**, scale **1:10000**, **Malmöhus län**, **Svedala**, **90 Segeån**,
**Limnologiska institutionen**, **Universitet i Lund**, and depth-archive
numbers **1157** and **3-1984**. Survey date, sounding method, number of
tracks/soundings and water level at measurement are visibly blank. The
identifier `3-1984` does not supply a 1984 survey date; the catalogue's 1983
is a drawing year. A contour labelled 5 is not a new independent maximum
measurement. A named vertical datum remains unresolved.

The separately received Swedish-language screenshot displays Havgårdssjön
**615365-134524**, district **SE4**, waterbody **NW615311-134527**, and literal
version **SVAR2016_3**. This qualifies the visible capture value, without
authenticating a backend version or another retained layer. It displays area
**0.5023 km²**, maximum depth **5.8**, mean depth **3.1** (no adjacent units
on either depth row), volume **1.67 miljoner m³**, and water-surface height
**50 m**. The two chart names and source text are clipped at the right edge;
the visible source prefix is **Limn inst**, while the complete TIFF legend
independently supplies the Lund institution. The screenshot contains
**1,379,367 bytes**, SHA-256
`5cac9abea0ef0da23d794cf99e4da2aa57d1d85e0fedd0367a4f83336ccdf96f`.
Its quantities are not merged with the catalogue's 0.540 km², 5.0 m maximum,
3.1 m mean and 1.670 volume for `3-1984`, or 5.8 m maximum for `2-0170`.
Conditionally interpreting the displayed volume and area in million m³ and
km² gives **16700/5023 m**, approximately **3.3247 m**, which rounds to
**3.3 m** rather than the displayed 3.1 **if that depth is in metres**.
This arithmetic does not establish a common measurement footprint, date or
water level, and supplies no repaired or preferred value.

The supplied preparation declaration identifies exact SMHI download routes
for [Havgårdssjön](https://vattenwebb.smhi.se/svarwebb/rest/downloadmap/615365-134524)
and [Finjasjön](https://vattenwebb.smhi.se/svarwebb/rest/downloadmap/622731-136920).
These are **user-declared source routes**, distinct from an independently
captured HTTP response. They do not replace the earlier Finjasjön screenshot's
unknown wire-captured download URL. Both packages remain in place, with only
local image derivatives used for direct comparison. No use licence, current
bathymetric accuracy, georeferencing, sediment support or field decision is
established by these received charts.

The received Östra Ringsjön ZIP `619626-135565-kartor.zip` contains **448,869
bytes**, SHA-256
`010ab253ce4b8e3c7123d8955e436d5692b89377ff093304e07d5c551757db53`.
All three TIFF members pass CRC checks. They are single-page, 1-bit, 600 dpi
scans, with no embedded GeoTIFF positioning or numeric depth grid. The original
ZIP remains in place. The TIFF bytes were rendered directly to local PNGs, and
full-chart/caption image comparisons were independently repeated; no original
TIFF was extracted or copied. The
[typed record](swedish-lake-chart-catalogue-context/source-records.json) binds
each member's identity and keeps this received context separate from the catalogue
rows.

The `3-0833` sheet is titled **DJUPFÖRHÅLLANDEN I RINGSJÖN** and shows several
connected basins, including the **SÄTOFTA** label. Its heading states measurements
in **1910–1911** and **1911–1912**, with water surfaces **+54,4** and **+54,0 M**
respectively. It supplies no named vertical datum or measurement method in that
heading. A faint handwritten scale is not selected as an authenticated ratio.
This broad historical plan is not treated as coextensive with either 1982 sheet.

The `3-2176` sheet, printed page **79**, **Fig. 2**, captions Östra Ringsjön at
**54.00 m.ö.h.**, with **Ekolodning** by **M. Enell**, **May–June 1982**, and
**X = maximum depth 16.4 m**. The `3-2177` sheet, printed page **78**, **Fig. 1
a–b**, separately names **Sätoftasjön**. Its panel a gives the same stated water
level, echo-sounding investigator and period, with **X = 17.5 m**. Panel b
depicts the extent of **organogenic (postglacial) sediments in Sätoftasjön**,
attributed to **Lodning** by M. Enell in May–June 1982. Both sheets have graphic
0–0.5–1 km scales. These captions qualify the 1982 survey period independently
of the catalogue's drawing-year column; neither the chart identifiers nor scan
timestamps supply survey dates. The sediment depiction is historical source
context, without a present-day sediment or coring-suitability claim.

The user also supplied a **Swedish register-panel transcription**, without a
register screenshot, API response or independently captured HTTP exchange. It
names lake **619626-135565**, district **SE5**, waterbody **SE619626-135565** and
version **SVAR2016_3**; that version remains a transcribed value rather than an
authenticated backend identity. It reports area **24.7556 km²**, maximum depth
**15** without a stated unit, and water-surface elevation **53 m**; mean depth
and volume are not supplied. Its chart notes explicitly distinguish `3-2176`
as **Östra Ringsjön excluding Sätoftasjön** and `3-2177` as the **Sätoftasjön
portion**. The user-declared
[SMHI download route](https://vattenwebb.smhi.se/svarwebb/rest/downloadmap/619626-135565)
identifies the supplied package's claimed origin; no additional GET or provider
checksum authenticates it in this review.

Keep the three chart extents and the transcription's quantities distinct. The
unlabelled register depth 15 is not substituted for either dated chart's marked
depth, and 53 m is not reconciled with 54.00 m.ö.h. by a one-metre correction:
no named common datum or level epoch has been established. None of the three
full scans prints a volume, area or mean-depth table. The catalogue's **1.247**
and **0.136** volume tokens and both mean-depth arithmetic disagreements therefore
remain unchanged, without multiplying by 100 or deriving replacements. Three
scans do not establish independent measurements of one common basin quantity.
The ZIP contains no separate licence member, and no explicit reuse licence is
printed on the inspected sheets. This factual account redistributes no chart,
raw raster or geometry and supplies no licence grant, digitized bathymetry,
current accuracy, selected core location or field decision.

## Comparison with retained registry attributes

The [retained 99-feature review registry](../../data/svar/review/sweden_lake_candidate_registry.geojson)
contains the same three literal `sjoid` values as the received panels. Its
`area_km2` and `sj_vatten_id` attributes are preserved separately from the
panel quantities and identifiers:

| Lake | Shared literal `sjoid` | Retained review `area_km2` | Received panel area, km² | Retained review `sj_vatten_id` | Panel waterbody identifier |
| --- | --- | --- | --- | --- | --- |
| Finjasjön | 622731-136920 | 10.497234 | 10.5085 | WA46511959 | SE622731-136920 |
| Havgårdssjön | 615365-134524 | 0.501745 | 0.5023 | WA79481388 | NW615311-134527 |
| Östra Ringsjön | 619626-135565 | 24.728453 | 24.7556 | WA76357027 | SE619626-135565 |

The Finjasjön panel values come from the supplied English browser capture
`Screenshot 2026-10-27 at 00.13.59.png`; Havgårdssjön's come from the Swedish
capture `Screenshot 2026-10-27 at 00.20.01.png`. Their exact original file
identities and translation/clipping limits are recorded above. Östra
Ringsjön's values remain the user's Swedish register-panel transcription,
without a screenshot or independently captured API response. The review
registry declares `generated_on: 2026-08-01`; neither that metadata date nor
the panel receipt dates establish measurement dates or a common source epoch.
The [existing normalized-file census](../../docs/report/source-relations/svar/normalized-export/feature-census.json)
already establishes exact typed matches for all 99 review rows on seven
declared fields, including `sjoid`, `sj_vatten_id` and `area_km2`. That
qualification is reused here; no full-file census or geometry comparison was
repeated.

These are three same-identifier comparisons of source statements. Common
geometry, area definition, measurement support, datum and observation date
remain unestablished. The area differences do not identify a temporal change,
a coordinate transformation, a unit conversion or a preferred value. The
retained WA identifiers and panel EU-style identifiers remain different fields;
no alias relationship or identifier crosswalk is authenticated by their shared
lake name or `sjoid`.

The present [SVAR collector](../../packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/svar/collection.py)
copies the WFS `AREA` scalar through numeric conversion into `area_km2` and
`SJVattenID` into `sj_vatten_id`. The present
[candidate producer](../../packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/candidate_registry.py)
inherits those normalized properties for its area screen; its representative
point is a separate geometry-derived value. Neither operation independently
recomputes polygon area. This code inspection describes the maintained
implementation. It does not authenticate the historical producer of the
retained export, recover its missing WFS pages, qualify provider units/CRS or
establish how the provider defined `AREA`. The retained review attributes and
all panel and catalogue quantities therefore remain unchanged.

The catalogue entries do not join pollen cores, establish palaeobasins,
qualify the retained 40,565-lake export, reconcile the historical 40,523-lake
population or change ranks. All forty questions and five unranked leads in
the field dossier retain their existing status; no access, permit, safety
or field decision has been supplied.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Factual archival catalogue and received Finjasjon, Havgardssjon and Ringsjon chart/survey/registry context, preserving separate chart scopes, source values, blanks, dated captions, scales and conditional volume/area checks without selecting a chart, corrected quantity or coring location. Three exact SJOID matches distinguish inherited review area attributes from supplied panel areas and keep WA SJVattenID and displayed EU-style identifiers separate. The current collector copies AREA rather than independently recomputing polygon area.

**Unsupported claim.** Current bathymetric accuracy or restrictions, a preferred/averaged depth or corrected water level, repaired Ringsjon volumes, an authenticated backend version or datum from a translated screenshot, inferred EPSG/sampling point, historical pollen-core/basin joins, exhaustive OCR absence, open geometry rights, changed ranks or field permission.

**Actual verification performed.** Original PDF/source-image qualification and failed downloader are preserved. Independent full-sheet/caption/legend comparisons and raw hash/CRC checks qualify eight TIFF members across three received lake ZIPs. Two registry screenshots and one user-pasted Ringsjon register transcription retain distinct provenance. The later Ringsjon captions name M. Enell, May-June 1982 and 54.00 m above sea level; the Satofta sediment panel has its own historical extent. No grid, digitization, source mutation or field decision was created. Independent Decimal JSON reading checked the three exact SJOIDs at feature indices23,34,66 in the unchanged200287-byte review registry; process exit0/.09s/RSS18595840B within5s/64MiB. The two original supplied screenshots were re-read visually, while Ostra remains a user transcription. Current collector/candidate source inspection establishes the implemented attribute path, not the old export producing epoch.

**Remaining input or review.** Dated chart context is available, including Ringsjon surveys in 1910-1912 and May-June 1982, but chart-specific datum, common quantitative support, current accuracy and intended reuse terms remain incomplete. Ringsjon charts provide no volume/area/mean-depth replacement for two catalogue discrepancies. Havgardssjon displayed V/A differs from displayed mean under the metre assumption; reported water levels remain separate. Resolver: SMHI/chart owner for exact chart identity, datum, reference levels, dates and use terms; field authority for current site, restrictions, access or permit decisions. Reopen when: Bind the intended chart and location to qualified datum/reference water level, measurement support, accuracy and use terms before quantitative or field use; preserve the two charts separately.

**Cause category.** data|comparability|access/rights

**Consequence.** Retain catalogue facts as unranked source context only, without changing the field dossier, historical or retained lake population, geometry authority, core identity, access or permit status.

**Precise next acceptance route.** Use each catalogue row, chart caption and registry statement within its actual source/extent/date. Quantitative use needs exact chart, common footprint, datum/reference level, accuracy and use terms; current field use additionally needs a source-bound selected location and applicable access, restrictions and permit decisions. Do not average maxima, rescale unexplained volumes, merge basins or transfer the historical Satofta sediment depiction to other extents or present conditions.

**Negative or refused result.** Original downloader remains exit 1/body_complete=false; ten catalogue blanks, two Ringsjon arithmetic disagreements, limited Bjaresjosjon text nonmatch and unresolved Uppakra identity remain. No supplied Ringsjon scan replaces the printed volume tokens or justifies rescaling by 100. Havgardssjon displayed ratio rounds to 3.3 rather than 3.1 under the metre assumption. No maximum, level correction, common datum, current sediment suitability or field approval is selected. Differing retained/panel area values establish neither a temporal change nor an authenticated WA/EU identifier crosswalk; provider field units/definitions and original export custody remain unqualified.

**Matched denominator.** Five original leads; three exact catalogue lake-number matches/five rows, one OCR-text nonmatch and one unresolved identity; ten blanks and three original conditional arithmetic checks. Three received lake packages contain eight TIFF members (seven chart scans and one survey sheet), two registry screenshots and one register transcription. The three Ringsjon chart extents remain separate; Havgardssjon display arithmetic is an additional conditional diagnostic. Separate keyed comparison: three existing lake IDs out of99review features, with three retained/panel area pairs and three distinct identifier-field pairs; no new census or geometry calculation.

Retained evidence: [reports/science/swedish-lake-chart-catalogue-context/source-records.json](swedish-lake-chart-catalogue-context/source-records.json), [data/svar/review/sweden_lake_candidate_registry.geojson](../../data/svar/review/sweden_lake_candidate_registry.geojson).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
