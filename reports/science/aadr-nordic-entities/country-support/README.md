# AADR country support and original sample context

The supplied McColl v2 paper and supplements are now available and have been read for the two exact country conflicts. They corroborate source labels and specimen relationships, but **neither conflicting coordinate record is corrected or admitted**. The existing [country report](report.json), [decisions](decisions.csv), selected AADR date fields and country products retain their existing meanings.

The source is McColl et al., *Steppe Ancestry in Western Eurasia and the Spread of the Germanic Languages*, [doi:10.1101/2024.03.13.584607](https://doi.org/10.1101/2024.03.13.584607), supplied v2 dated 7 January 2025. Original `media-1.xlsx`, archaeological `media-2.pdf` and genetics `media-15.pdf` are consumed in place. The archaeological material is **S7** in this version; genetics page 22 is **S4, Imputation**. Earlier HTTP 403 attempts remain historical retrieval failures, not a current claim that these supplied files are missing.

[mccoll-source-context.json](mccoll-source-context.json) retains the compact factual crosswalk, original byte identities, source literals and actual checks. It omits the original attachments, complete worksheets and genetic measurements. The full literal-cell observation stays under repository artifacts.

The paper title page identifies a preprint, not certified peer review, under CC BY-NC-ND 4.0. No blanket attachment redistribution grant is inferred. Original PDFs and workbook are not copied into product content. This account retains scoped factual source metadata, conflicts and citations, without genotype results or an inferred open-data licence for the attachments.

## Cited study and supplied companion

The retained AADR annotation cites the **unversioned Celtic study**,
[*Tracing the Spread of Celtic Languages using Ancient Genomics*,
DOI 10.1101/2025.02.28.640770](https://doi.org/10.1101/2025.02.28.640770).
The supplied Germanic paper above is a **distinct DOI study**, whose v2 is
independently identified as 7 January 2025. Matching CGG, museum and site fields
provide companion-source context; they do not make the publications version
aliases or establish a correction to the AADR annotation.

The [official Celtic bioRxiv metadata](https://api.biorxiv.org/details/biorxiv/10.1101/2025.02.28.640770)
records v1 on **1 March 2025**, v2 on **2 May 2025** and v3 on **8 May 2025**.
Each reports literal licence `cc_by_nc_nd` and `published=NA`. The
[Crossref metadata](https://api.crossref.org/works/10.1101%2F2025.02.28.640770)
also identifies the Celtic DOI and CC BY-NC-ND 4.0, with an empty relation object.
Those are provider metadata states, **not proof of journal-publication absence**.
The AADR citation does not identify a version; present v3 cannot be assigned as
its source by default.

A bounded acquisition on 26 October 2026 retained exactly **six GET responses**
in the shared source store at `adna/celtic-source/2026-10-26/`. Its ordinary
`source-manifest.json` records actual request/final URLs, response headers,
UTC boundaries, byte counts and SHA-256 values. All six bodies were closed and
rehashed, totaling **46,276 bytes**, without redirects, retries, challenge
bypass, login or outreach. Three responses were HTTP 200 publication metadata
from bioRxiv, Crossref and Europe PMC. The advertised Europe PMC main-PDF route
returned **403**, its documented full-text XML API returned **500**, and the
original bioRxiv v1 supplement page returned **403**. These failed response
bodies are not article or specimen-table content. Europe PMC's PPR984375 metadata
labels the main record open access and `hasSuppl=N`; those labels did not deliver
the requested main or attachment bytes. Those six requests opened no Celtic
specimen table or genetic measurements, and no already supplied Germanic original was copied. The later
supplied v3 package is consumed separately below.
The [publication provenance section](mccoll-source-context.json) retains these
facts separately from the earlier successful Germanic and museum evidence.

A **separate two-GET metadata follow-through** retained the public
[Cambridge accepted-record page](https://www.repository.cam.ac.uk/items/0f0cbcd9-9d79-4820-8221-1fb254b9b4b9)
and a bounded exact-title Crossref journal query. Both returned HTTP 200;
the closed bodies total **485,087 bytes** under
`adna/celtic-source/accepted-record-metadata-2026-10-26/`, with their own
`source-manifest.json`. This does not enlarge or rewrite the historical
six-response unit above. No embargoed manuscript or specimen attachment was
requested, and no genetic measurements were opened.

The Cambridge item, handle **1810/409414** and repository DOI
**10.17863/CAM.135565**, is titled *Tracing the spread of Celtic languages using
ancient genomics*. Its metadata gives version **AM**, displays **Accepted
version** and **Peer-reviewed**, and names **Nature** / **Nature Research**.
Acceptance is **22 September 2026**, repository deposit **8 October 2026**,
and accession **13 October 2026 at 23:30:42 UTC**. These are distinct events:
the HTML `citation_publication_date` repeats accession and does not establish
a journal-publication date. The file is **embargoed until 13 October 2029**.
Public item metadata says CC BY 4.0; that is not a grant to access or
redistribute the embargoed file and does not replace the preprint's separate
CC BY-NC-ND metadata.

Matching title and authors support an accepted-record counterpart. The exposed
metadata contains no journal DOI/version-of-record field or Celtic preprint
DOI token, so it does not explicitly bind a preprint version or the retained
AADR annotation. The Crossref query returned three unrelated titles; this is
a bounded negative lookup, not proof that no journal DOI or publication exists.
The compact JSON keeps both metadata requests and these limits separate from
the supplied Germanic source and original Celtic attempts.

AADR's date/coordinate strings remain **annotation assertions**; the earlier
worksheet cells and archaeological paragraphs below remain **Germanic v2
source context**; and museum records remain **locality/assemblage context**.
The additional Celtic v3 package now supplies a descriptive combined Fauskland
row. It does not identify which Celtic version the unversioned AADR citation
used or select a date, coordinate or admission decision.

## Supplied Celtic v3 sample metadata

The complete supplied package identifies the Celtic DOI above, **v3 posted
8 May 2025**. Its main PDF has 38 nonempty extracted pages; the two wide figure
PDFs each have one intentionally oversized page, and the notes PDF has 81.
All five original byte identities are retained in the compact JSON's
`supplied_celtic_v3` section. The workbook passed ZIP CRC checks and contains
eleven sheets. The main title page states CC BY-NC-ND 4.0 and that this preprint
was not certified by peer review; originals remain outside product content.
This local source receipt does not establish live-server byte equality or an
exhaustive publisher attachment list.

Direct original ZIP/XML reading covers all **4,587 sample rows** in
`S1.1. Sample metadata` (`A1:AG4588`). Exactly one row contains the named
Fauskland CGG aliases: physical Excel **row 4237**. Sixteen descriptive fields
were independently decoded through the unchanged maintained workbook reader.
Other numerical results sheets were inventoried, without scientific validation.

| Source field | Literal Celtic v3 value |
| --- | --- |
| `sampleId` | `CGG105916_CGG105917_CGG105918.mccoll_230821_ironage` |
| `popId` / `versionID` | `CGG105916_CGG105917_CGG105918` / `CGG105916` |
| `site` / `country` | `Fauskland` / `Norway` |
| `latitude` / `longitude`, native numeric XML | `63.605789999999999` / `14.858610000000001` |
| `dataSource` | `thisPublication` |
| `ageHigh` / `ageLow` / `ageAverage` | `4087` / `3934` / `4011` |
| `datingSource` / `age14C` / `ageRaw` | `direct` / literal `NA` / literal `NA` |

The combined alias and summary fields agree with Germanic S5.1 row 2323.
The numeric coordinates agree with the original AADR Fauskland pair and retain
the conflict with its Norway locality and the museum point. The source does
not identify an exact sampled museum subrecord. `thisPublication` is a source
label; the explicit companion reuse described below means it cannot establish
an independently sampled person. The combined representation is one previously
reported individual, not three new independent observations.

The selected headers and row do not state an age unit/reference epoch,
calibration curve or laboratory identifier for these summary fields. Main-text
BP notation does not resolve that missing table-specific information. Preserve
the literal values alongside AADR's distinct `4503` mean, `134` SD and full-date
string; no recalibration, date conversion or rounding repair is performed.

No `105915`, `Aunvollen`, `T11792`, `A7437` or `T20248` match occurs in this
finite S1.1 sheet. That establishes a scoped metadata nonmatch, without implying
absence from every auxiliary results sheet, publication or release. In
particular, it cannot explain the retained Aunvollen **Individual 2** annotation.

The main paper's Methods, PDF page 28 lines 607–609 and page 29 lines 627–634,
explicitly reuse the Germanic companion's dataset and refer site/sampling details
to reference 41. Data availability on PDF page 31 lines 674–677 points to
PRJEB87274 and the accompanying paper's **Note S4**. The supplied Germanic v2
archaeological section is **S7**; the differing pointer is preserved. Celtic
v3's own **S4** concerns Y chromosomes. Its **S6**, read in full on notes
PDF pages 57–62, discusses Urnfield, Hallstatt and La Tène interpretation; it
supplies no named Norwegian specimen catalogue. Searches of the complete main
and notes text found no named CGG/site/museum terms above. Neither that bounded
text result nor the general archaeological discussion replaces the missing
specimen/laboratory/date/coordinate crosswalk.

Source extraction and direct XML inspection terminated successfully in 6.26 s,
peak RSS 221,609,984 bytes. A second decoder plus direct original ANNO comparison
terminated successfully in 2.66 s, peak RSS 318,341,120 bytes: all 16 selected
Celtic fields and the four retained AADR rows agree with their scoped source
observations. Five supplied originals were authenticated before and after;
selected AADR fields remain unchanged. These observations used the committed
reader at `19feb79bf`, shared Python environment, bytecode suppression,
one-thread settings and 120 s / 512 MiB posthoc bounds. The literal observations
and six original-page previews remain under
`artifacts/celtic-source-review/`; the compact JSON records tool handles and
resources. No genetic analysis, coordinate transformation or scientific
admission was performed. The earlier failed remote requests and Cambridge
embargo context remain intact as separate historical evidence.

## Retained specimen and annotation comparison

The existing coordinate comparison treats the two AADR latitude/longitude pairs on the pinned boundary degree axes and obtains Sweden while their source political entity is Norway. That is an uncorrected source/boundary conflict. Native coordinate datum, positional accuracy, archaeological locality meaning and the authority to select a replacement remain unqualified.

| AADR genetic ID | Table S1.1 physical row | Original specimen identity | Table locality and coordinates |
|---|---:|---|---|
| `CGG_2_105915.SG` | 575 | `CGG_2_105915`; `A7437/T20248 Individual 2`; tooth/M1; age at death 35–49 | Aunvollen; Norway; latitude `63.12322`, longitude `16.90684` |
| `CGG_2_105916.SG` | 588 | `CGG_2_105916`; `T11792c`; tooth/M1 | Fauskland; Norway; latitude `63.60579`, longitude `14.85861` |

Archaeological S7 PDF/printed page 161, lines 3047–3062, instead prints the Aunvollen/T20248 coordinate pair `64.1641, 11.8140`. It describes three individuals from the grave: an infant of approximately 1–1.5 years, a young woman of 19–20 years and an older woman of 35–49 years. Their date entries are distinct:

| S7 individual description | Source date literal | Source laboratory token |
|---|---|---|
| Infant | Modern | `Tra – 14441` |
| Young woman | 651–759 CE | `Tra14912` |
| Older woman | 649–673 CE | `Tra15329` |

The 35–49-year description in worksheet row 575 is consistent with the older-adult description, but the inspected source does not explicitly bind **Individual 2** to `Tra15329`. Sharing museum identifier T20248 does not assign one individual's date to another. The prior author isotope workbook likewise distinguished juvenile/old/young adult material and supplied no CGG/Individual 2 crosswalk; its separate coordinate context is not overwritten here.

Table S1.1 row 575 gives context date `800-1050AD`, calibrated-BP columns `1150`, `900`, `1025`, and literal `NA` for laboratory number, radiocarbon age and its error. The retained AADR representation labels a direct IntCal20 date with a missing-laboratory warning, mean `943`, SD `134`, and full-date string `800-1050 calCE (1025±125 BP)`. These are source discrepancies to retain, not a basis to select the older woman's seventh-century date or relabel the table context as a measured radiocarbon determination.

Archaeological S7 pages 174–175 describe Fauskland gnr 8/1, T11792c, on Hitra. The printed coordinate pair remains `63.6057, 14.8586`; it does not supply a correcting Norwegian point. The source describes disturbed gravel/tidal recovery and a skeleton represented by fragments, skull and jaw. Its anatomical and genetic identifiers must be read together:

| Table S1.1 row | Native ID | Tooth | Native flag |
|---:|---|---|---|
| 588 | `CGG_2_105916` | M1 | `merged_CGG105916_CGG105917_CGG105918` |
| 589 | `CGG_2_105918` | M3 | same merged flag |
| 590 | `CGG_2_105917` | M2 | same merged flag |

S7 page 175 line 3359 prints `CGG_2_105917T` with a trailing **T** for M2. That literal differs from the worksheet identifier and is not silently normalized. The genetics supplement's physical PDF page 22, lines 408–413, explicitly identifies the three CGG samples as merged data for **one individual**, represented by four worksheet lines. They are not three independent people.

Table S1.1 row 745 is the combined `CGG_2_105916_CGG_2_105917_CGG_2_105918` record. Its museum, country, site, coordinates and dating fields are literal `NA`; those cells are not filled from another row. Its `sampleId` and `popId` bind the combined alias. Table S5.1 row 2323 supplies that same combined sample/pop alias, `versionID=CGG105916`, Fauskland, Norway and coordinates `63.60579, 14.85861`. This is source-backed representation/merger context, not an automatic crosswalk that rewrites the selected AADR record. ENA's previously retained combined alias remains consistent with the merged representation.

S7 page 175 lines 3361–3363 gives skull `3682+/-12 BP (Tra 17220)` and jaw `3682±13 BP (TRa 17221)` as dates of the same individual. Table S1.1 row 588 instead reports radiocarbon string `3680 & 3680`, errors `10 & 15` and laboratory string `TRa-17220 & TRa-17221`; rows 589–590 report `3680` and `10`. All three have calibrated-BP columns `4087`, `3934`, `4011`. S5.1 row 2323 retains numeric `4087.0`, `3934.0`, `4011.0` and dating-source label `direct`. The AADR representation retains mean `4503`, SD `134` and full date `2137-1984 calBCE (4010±76 BP, TRa-17220 & TRa-17221)`. No averaging, rounding repair, reservoir adjustment, calibration or chronology replacement is performed.

The coordinate columns in S1.1 are shared-string cells; S5.1's coordinate and age-summary cells are native numeric tokens. Literal `NA`, a physically present blank cell and an absent cell remain distinct. Original formulas/caches, types, styles, row references and headers are retained by the narrow maintained reader. It reads only the requested six descriptive rows and the two exact AADR IDs in both original annotation panels; it does not expose genetic measurements.

The maintained reader consumed committed source `ac1c3619a9e16c4450f40d945a01d847a060b0e5` once. Owned execution session 59042 terminated with exit 0 in 1.984734667 s; producer time was 1.327406792 s and macOS `/usr/bin/time -l` peak RSS was 308019200 bytes. The saved `native-run/context.json` is 101542 bytes, SHA-256 `8a86a900655dfda0e6addba95dcb6c84b5815e9e3456d53ed0478be309766a49`. Exact command, explicit Python `-B`, bytecode suppression, one-thread settings and UTC boundaries are recorded in `artifacts/physical-core/mccoll-country-context/native-execution/execution.json`. The run satisfied its 60 s / 512 MiB posthoc / 1 MB context budgets. Four original file identities, both AADR source bodies, existing country report/decisions and consumed source revision were checked before and after reading; the exact parsed workbook buffer was also authenticated.

The separately committed direct original ZIP/XML/CSV observer ran once on those saved bytes, without re-running the reader. Owned session 21988 terminated with exit 0 in 1.450032834 s, peak RSS 284737536 bytes. It checked all four original identities, six worksheet rows, 162 descriptive cells including native types/formulas/cache/blank states, four original AADR rows and exact equality of the two saved country-conflict dictionaries to the existing CSV. Before/after source identities, native context bytes and source revision remained unchanged. Its 206-byte passed result is at `artifacts/physical-core/mccoll-country-context/independent-check/check.json`; exact command and resource facts accompany it in `independent-execution/`. Ten controlled tests, configured Ruff and strict mypy passed, including refusal of a workbook changed before parsing, a PDF changed after parsing and an AADR input changed after reading. This qualifies the scoped machine observation; the observer does not independently interpret archaeological prose or admit country/chronology claims.

The original ANNO physical-line locators include the header: 1240k 20621/20622 and HO 25126/25127. The existing decision ledger's inherited source-row identifiers remain unchanged rather than being replaced with these physical-line locators. Both annotation panels retain the same descriptive literals for each of the two IDs.

Narrow original-page text extracts and four renders were inspected at archaeological PDF/printed pages 161, 174, 175 and genetics physical PDF page 22. These derivatives remain only under `artifacts/physical-core/mccoll-country-context/source-pages/` for original-page comparison. The four original files are identified by streamed byte counts and SHA-256 values, without copying them or treating filesystem receipt time as the publication date. PDF claims above are scoped to the named site paragraphs; unrelated Jøa material lower on page 175 is not assigned to Fauskland.

## Museum locality and collection evidence

The supplied [Fauskland catalogue record T11792:c.003](https://collections.vm.ntnu.no/artefacts/13439-T11792-c-003)
was inspected through three user screenshots of its identity, coordinates,
find circumstances and map. The supplied museum-generated factsheets for
[Aunvollen human T20248:L.012](https://collections.vm.ntnu.no/artefacts/175301-T20248-L-012)
and [dog T20248:L.013](https://collections.vm.ntnu.no/artefacts/175300-T20248-L-013)
were read in full and their human pages and dog page visually checked.
Two dog exports have identical extracted text and describe the same record.
Direct web-tool access to the two human record URLs failed; no independent
API response, Fauskland PDF export or complete museum catalogue was acquired.
The supporting Spor magazine was a discovery lead; it is not the authority
for the following specimen-record fields.

[museum-source-context.json](museum-source-context.json) records the six
original file identities, literal coordinate/precision labels and three
museum-record contexts. Originals remain in place outside product content;
no screenshots, photographs or full factsheets are redistributed.

| Museum record | Displayed latitude / longitude | Precision label | Collection link |
| --- | --- | --- | --- |
| Fauskland `T11792:c.003` | `63.6058590629654 / 8.8588817461179` | `Funnsted (Lokalitet)` | Human skeletal assemblage; Hitra, Fauskland 8/1 |
| Aunvollen `T20248:L.012` | `64.1635647815224 / 11.819740680260399` | `Bruk` | Human collection explicitly numbered `A.7437`; Aunvold, Steinkjer 246/1 |
| Aunvollen `T20248:L.013` | same displayed pair | `Bruk` | Separate adult dog material; no human CGG identity |

The common coordinate label is literally **`Coordinate (EU89 - Lat/Lon)`**.
Fauskland's record update is displayed as 26 October 2026; human L.012 as
2026-03-06 and dog L.013 as 2026-10-26. A screenshot filename is not a verified
HTTP retrieval time. Locality and property precision are categorical source
descriptions, not metric uncertainty radii. Many decimals do not establish
survey accuracy. Kartverket distinguishes [EUREF89 and dynamic WGS84 reference
frames](https://www.kartverket.no/til-lands/posisjon/referanserammer-for-noreg);
that source does not authenticate the museum's abbreviated label, exact
realization, EPSG code or acquisition epoch. Preserve the literal label before
any explicitly declared coordinate transformation or nominal spatial comparison.

The Fauskland museum longitude is source-owned evidence distinct from both
paper values near `14.8586`; it is not a guessed six-degree adjustment.
Museum root T11792c, human material, locality and cadastral 8/1 agree with the
paper assemblage. The inspected paper does not explicitly name subrecord
`c.003` for a sampled M1/M2/M3 tooth, so the exact subrecord/sample crosswalk
is narrower than the demonstrated assemblage link. The catalogue's disturbed
tidal/gravel context is consistent with the archaeological account; neither
source's recovery prose resolves the conflicting numerical date fields.

The Aunvollen human factsheet explicitly says return from the Schreiner
Collection in 2022 revealed **two different individuals**, with duplicated
skeletal elements. Its initial probably-female age of 19–20 cannot be assigned
to both. It establishes the A.7437 collection link without identifying the
paper's 35–49-year **Individual 2**, sampled M1 or radiocarbon laboratory token.
The dog is separate animal material. Both factsheets describe a grave about
150 m north of the farm buildings, excavation in 1981 and recovery of further
material in 1982. These are discovery/collection dates and relative locality
descriptions; they do not select an ancient date or justify moving the property
point. The archaeology supplement's `64.1641 / 11.8140` point remains separate.

The existing committed country helper was then applied to all three museum
records and both original AADR pairs, with each pair independently treated as
literal degrees on the pinned Natural Earth 5.1.1 boundary axes. All three
museum records give strict Norway containment; both original AADR pairs retain
strict Sweden containment with `raw_country_conflict`. The human and dog share
one property point, so three records represent only two distinct museum points.
No source coordinate was merged or selected. This is an explicitly nominal
degree-axis comparison, with **no datum transformation** or museum-label/EPSG
authentication; it is not a newly admitted archaeological map layer.

The comparison consumed committed source and curated input at
`679389cd4`, exited zero in 0.88 s process time, and measured 86,065,152 bytes
peak RSS. Original museum files, boundary inputs, the existing country report
and decisions were authenticated before and after; HEAD stayed unchanged.
The [compact source context](museum-source-context.json) retains all five
outputs, source/parameters, resource facts and evidence limits. No new
independent polygon oracle was run: this reuses the already checked, unchanged
country helper. An initial attempt failed at import because the environment
has no Shapely, before reading inputs. Its literal failure remains under
`artifacts/source-review/museum-localities/spatial-check/`; the successful
comparison is separately retained in `degree-axis-check/`. No dependency was
installed or result overwritten.

The remaining exact conditions are specimen-level binding and coordinate
semantics for any selected correction, an explicit Aunvollen Individual 2
laboratory/date crosswalk, and qualified treatment of inconsistent Fauskland
and AADR dating representations. The sources resolve document availability,
museum locality evidence, human/animal distinction and documented merger
subquestions. Country/map/chronology admission and field decisions remain open.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Literal source comparisons for the two AADR country conflicts, author-reported Fauskland three-sample/one-individual merger, distinct Aunvollen individuals, museum locality/collection context and nominal pinned-boundary comparisons; no coordinate or chronology selection. Supplied Celtic v3 row 4237 supplies the combined Fauskland representation; all 4587 S1.1 rows have a scoped search and main Methods explicitly reuse the distinct Germanic companion.

**Unsupported claim.** Treating the Germanic and Celtic DOIs as version aliases, correcting AADR coordinates or dates, assigning the older Aunvollen woman to Individual 2, counting merged teeth as independent people, genotype inference, qualified country/map/chronology admission or field permission.

**Actual verification performed.** Committed reader ac1c3619a and independent original ZIP/XML/CSV observer each exited zero: six Germanic worksheet rows, 162 descriptive cells, four AADR panel rows and two unchanged country decisions. Original archaeological pages 161/174/175 and genetics page 22 were visually checked. Museum source facts and a separate nominal five-pair degree-axis comparison were retained. Six bounded Celtic GET responses supplied three publication-metadata successes and three failed content responses, not a Celtic specimen table. A separate two-GET metadata unit retained the Cambridge Nature accepted-record HTML and a bounded Crossref query, both HTTP 200; original metadata bodies were rehashed without fetching the embargoed file. Acceptance/deposit/accession and item rights remain distinct from publication, file access and preprint-version binding. No new polygon oracle, datum transformation or genotype analysis was performed. Later user-supplied Celtic v3 originals were read in place: PDFs 38/1/1/81 nonempty pages, workbook CRC and eleven-sheet inventory, all 4587 S1.1 rows searched. Direct ZIP/XML and a separate unchanged reader agree on 16 descriptive fields; direct original ANNO reading agrees on all four retained rows. Original title, Methods and data-availability images were independently compared. Five byte identities and previous source context are preserved; no genetic results-sheet analysis or source copy was performed.

**Remaining input or review.** The supplied Celtic v3 metadata now bind the combined Fauskland alias, but the unversioned AADR citation does not identify its actual Celtic version. AADR assertions, Germanic companion cells, Celtic v3 row and museum localities retain different date/coordinate scope. Exact individual/laboratory/subrecord links, datum/precision and correction authority remain unresolved. Resolver: Source custodian for the versioned Celtic specimen crosswalk and museum/sample identity; chronology and geography reviewers for any proposed scientific or map correction. Reopen when: Bind the cited Celtic version and sample-owned laboratory/date/coordinate representations, exact museum subrecord/individual links and an explicit datum/precision and correction decision.

**Cause category.** data|comparability|access/rights|qualified review

**Consequence.** Retain annotation, companion-study and museum contexts separately, with unchanged country products, source coordinates and selected AADR fields; permit source reading without promoting map, date or biological claims.

**Precise next acceptance route.** Use the existing literal-source and country-support consumers for their stated scopes. Any correction must cite the exact Celtic/specimen and museum bindings and explicit chronology/datum authority; re-run only the affected admitted downstream consumer after that decision. Original publisher attachments remain outside public product content.

**Negative or refused result.** Both original AADR pairs still conflict with source Norway on the pinned boundary axes; all date disagreements and the trailing-T alias remain. Museum locality/property points are not sample corrections. Celtic PDF/XML/supplement attempts returned 403/500/403; the earlier missing-Shapely attempt is preserved. No admission was granted. The later supplied package supersedes the earlier table-availability gap. No 105915 or Aunvollen match occurs in its S1.1 sheet; this is a finite nonmatch, not universal absence. Row 4237 retains the conflicting 14.85861 longitude and literal 4087/3934/4011 summaries; its headers/row do not bind units, calibration or laboratory identifiers.

**Matched denominator.** Two AADR IDs in two original annotation panels; six Germanic worksheet rows and 162 descriptive cells; three museum records at two distinct points, including one separate dog; five nominal point comparisons. Fauskland three sampled teeth plus a merged row represent one author-reported individual. Additional Celtic v3 source: 4587 S1.1 sample rows searched, one combined Fauskland target row with 16 independently decoded descriptive fields, zero 105915 matches. This is the previously reported merged individual, without another independent biological observation.

Retained evidence: [reports/science/aadr-nordic-entities/country-support/report.json](report.json), [reports/science/aadr-nordic-entities/country-support/decisions.csv](decisions.csv), [reports/science/aadr-nordic-entities/country-support/mccoll-source-context.json](mccoll-source-context.json), [reports/science/aadr-nordic-entities/country-support/museum-source-context.json](museum-source-context.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
