# Archival lake-chart context for the Swedish field leads

SMHI's *Svenskt Vattenarkiv: Sjökartor och sjöuppgifter, Register 1987*
provides five separate chart entries for three of the four identified lake
leads in the [existing field dossier](../needed/field-decisions.md). The
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
received Finjasjön chart scans are described separately below; the other
lakes remain catalogue-only context.

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
volume, area and mean depth remains **unqualified** until the actual charts,
reference levels and source meaning support it. Rounding agreement in the
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
Finjasjön survey sheet does not fill their blank cells.

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

The catalogue entries do not join pollen cores, establish palaeobasins,
qualify the retained 40,565-lake export, reconcile the historical 40,523-lake
population or change ranks. All forty questions and five unranked leads in
the field dossier retain their existing status; no access, permit, safety
or field decision has been supplied.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Factual archival chart-catalogue transcription and separately received Finjasjon chart/survey-sheet and translated registry context, preserving original rows, blanks, dates, scales, source levels and conditional exact volume/area arithmetic without selecting a chart or coring location.

**Unsupported claim.** Current bathymetric accuracy or restrictions, a preferred/averaged depth or corrected water level, repaired Ringsjon volumes, an authenticated backend version or datum from a translated screenshot, inferred EPSG/sampling point, historical pollen-core/basin joins, exhaustive OCR absence, open geometry rights, changed ranks or field permission.

**Actual verification performed.** Original PDF offline/source-image qualification and exact conditional arithmetic are retained, including the failed downloader. New 502622-byte ZIP has three authenticated TIFF members: two charts and one survey-description sheet. Independent full-chart/legend/scale and screenshot comparisons verify factual transcription; 1986 and minus0.2m survey conditions belong to5807b. No grid, digitization, geometry, source mutation or field decision was created.

**Remaining input or review.** Received Finjasjon scans supply source context and a1986 survey sheet, but0818 survey date, vertical datum, current accuracy and intended chart/geometry reuse terms remain unbound. Screenshot42m and5807 printed mean+43.00 remain separate; two Ringsjon catalogue volume/area ratios still disagree with printed means. Resolver: SMHI/chart owner for exact chart identity, datum, reference levels, dates and use terms; field authority for current site, restrictions, access or permit decisions. Reopen when: Bind the intended chart and location to qualified datum/reference water level, measurement support, accuracy and use terms before quantitative or field use; preserve the two charts separately.

**Cause category.** data|comparability|access/rights

**Consequence.** Retain catalogue facts as unranked source context only, without changing the field dossier, historical or retained lake population, geometry authority, core identity, access or permit status.

**Precise next acceptance route.** Use the retained catalogue and received scans as factual source context. Quantitative use requires exact chart/datum/reference-level/accuracy/use binding; field use additionally needs a source-bound selected location and current applicable access, restriction and permit decisions. Do not fill blanks, merge charts or transfer5807 dates/levels to0818.

**Negative or refused result.** Original downloader remains exit1/body_complete=false; ten catalogue blanks and two arithmetic disagreements remain. Bjaresjosjon text nonmatch and unresolved Uppakra identity remain limited findings. The earlier Finjasjon text reader exposed no attributes; received translated screenshot evidence does not authenticate its backend version. No preferred chart, corrected level, numeric grid or field approval.

**Matched denominator.** Five existing leads; three exact catalogue lake-number matches/five chart rows, one OCR-text nonmatch and one unresolved identity; ten blanks and three conditional arithmetic checks. Additional Finjasjon ZIP contains two chart scans and one survey sheet, with one separately received translated registry screenshot.

Retained evidence: [reports/science/swedish-lake-chart-catalogue-context/source-records.json](swedish-lake-chart-catalogue-context/source-records.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
