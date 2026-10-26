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
whether they cover the same extent or reference water level. The actual
charts and bathymetric grids were not acquired.

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
levels remain unreported here, and present chart availability is unverified.

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
public access. The documented
[current Finjasjön record route](https://vattenwebb.smhi.se/svarwebb/?sjoid=622731-136920)
did not expose readable current attributes in the available text reader;
its current SVAR version, attribute source and bathymetric fields remain
unverified. Current individual-record routes for the other leads were not
queried. No undocumented API was used to replace these limitations.

The catalogue entries do not join pollen cores, establish palaeobasins,
qualify the retained 40,565-lake export, reconcile the historical 40,523-lake
population or change ranks. All forty questions and five unranked leads in
the field dossier retain their existing status; no access, permit, safety
or field decision has been supplied.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Factual archival chart-catalogue transcription for predeclared lake-number leads, preserving separate rows, blank cells, source-page locators and conditional exact volume/area arithmetic without selecting a chart or coring location.

**Unsupported claim.** Current bathymetry or survey dates, a preferred/averaged lake depth, repaired Ringsjon volumes, an EPSG or sampling point inferred from outlet identifiers, historical pollen-core/basin joins, exhaustive absence from OCR text, open geometry rights, changed ranks or field permission.

**Actual verification performed.** Offline qualification checked the sole retained 4,226,310-byte PDF against declared length/hash, header/EOF and 180-page pdfinfo output, preserving the original downloader failure. Independent rendered-page comparisons at indexes 2/27/85/86/87 checked definitions and all five chart rows. Exact conditional arithmetic gives Havgardssjon 167/54 m matching printed rounding and Ringsjon 1247/20220 m and 4/125 m disagreeing with the printed means. No chart/grid, new lake export, undocumented API or numeric confidence interval was created.

**Remaining input or review.** The 1987 catalogue supplies source chart rows, not current surveys or bathymetric grids. Chart extents/reference levels, measurement dates and permission for intended chart/geometry reuse are unbound; two printed Ringsjon volume/area ratios disagree with printed mean depths under the stated unit interpretation. Resolver: SMHI/source chart owner for chart meaning, reference levels, dates and use terms; field authority for any separately requested location, access or permit decision. Reopen when: Obtain and identify the actual relevant chart/attributes with extents, reference water level, measurement epoch and allowed use; bind an exact lake/core/location before quantitative or field use.

**Cause category.** data|comparability|access/rights

**Consequence.** Retain catalogue facts as unranked source context only, without changing the field dossier, historical or retained lake population, geometry authority, core identity, access or permit status.

**Precise next acceptance route.** Use the retained transcription as a source lead now. Quantitative lake use requires the actual chart/reference-level/source-meaning evidence; field use additionally requires a selected, source-bound location and explicit applicable access/permit decisions. Do not fill blanks, repair printed volumes or infer current geometry from the catalogue.

**Negative or refused result.** Original acquisition remains exit 1 with body_complete=false despite readable retained bytes; it was not retried or relabelled successful. Ten blanks remain null; two volume/area/mean-depth combinations are unqualified. Bjaresjosjon exact ID was not found in available text, without an absence claim; Uppakra lacks a unique lake ID. The available current Finjasjon route did not expose verified attributes.

**Matched denominator.** Five existing field leads; three exact positive lake-number matches with five separate chart entries, one OCR-text nonmatch and one unresolved lake identity. Ten blank cells and three conditional volume/area checks remain explicit; charts are not independent repeated measurements.

Retained evidence: [reports/science/swedish-lake-chart-catalogue-context/source-records.json](swedish-lake-chart-catalogue-context/source-records.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
