# AADR country support and original sample context

The supplied McColl v2 paper and supplements are now available and have been read for the two exact country conflicts. They corroborate source labels and specimen relationships, but **neither conflicting coordinate record is corrected or admitted**. The existing [country report](report.json), [decisions](decisions.csv), selected AADR date fields and country products retain their existing meanings.

The source is McColl et al., *Steppe Ancestry in Western Eurasia and the Spread of the Germanic Languages*, [doi:10.1101/2024.03.13.584607](https://doi.org/10.1101/2024.03.13.584607), supplied v2 dated 7 January 2025. Original `media-1.xlsx`, archaeological `media-2.pdf` and genetics `media-15.pdf` are consumed in place. The archaeological material is **S7** in this version; genetics page 22 is **S4, Imputation**. Earlier HTTP 403 attempts remain historical retrieval failures, not a current claim that these supplied files are missing.

[mccoll-source-context.json](mccoll-source-context.json) retains the compact factual crosswalk, original byte identities, source literals and actual checks. It omits the original attachments, complete worksheets and genetic measurements. The full literal-cell observation stays under repository artifacts.

The paper title page identifies a preprint, not certified peer review, under CC BY-NC-ND 4.0. No blanket attachment redistribution grant is inferred. Original PDFs and workbook are not copied into product content. This account retains scoped factual source metadata, conflicts and citations, without genotype results or an inferred open-data licence for the attachments.

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

The remaining exact conditions are a specimen-owned, versioned authority for coordinate meaning/datum and any correction, an explicit Aunvollen Individual 2 laboratory/date crosswalk, and qualified treatment of the inconsistent Fauskland and AADR dating representations. This source unit resolves the availability and documented merged-individual subquestions. It does not resolve country/map/chronology admission, infer corrected coordinates or make a fieldwork permit or locality decision.
