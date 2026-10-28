# Obishir V specimen chronology

The governed [radiocarbon supplement](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/adna/governance/source_library/papers/10.1038-s41562-021-01083-y/supplementary/41562_2021_1083_MOESM1_ESM.pdf), SHA-256 `d6fcdfae2d835883c68585aa6ff87ad197cc8561c434f654099322fefeb156a9`, identifies three directly dated teeth by specimen number in Supplementary Table 2, page 11. Official ENA BioSample aliases supply the accession-to-specimen join. The calibrated intervals are two-sigma ranges; the separate measurements are uncalibrated 14C BP.

| ENA accession | Specimen | Lab | 14C BP | Calibrated interval | Decision |
| --- | --- | --- | --- | --- | --- |
| `SAMEA8022721` | `OB20-06` | `AA-114606` | 7012 ± 45 | 5991–5771 cal BCE | Direct specimen interval admitted |
| `SAMEA8022724` | `OB20-04` | `AA-114607` | 4260 ± 36 | 3003–2701 cal BCE | Direct interval admitted with the source's stratigraphic inconsistency warning |
| `SAMEA8022722` | `OB21-04` | `AA-114608` | 2796 ± 34 | 1045–835 cal BCE | Direct specimen interval admitted; source taxon is *Capra hircus*, so sheep publication remains blocked |
| `SAMEA8022720` | `OB20-01` | — | — | — | No source-matched specimen interval admitted |
| `SAMEA8022723` | `OB21-06` | — | — | — | No direct specimen date found |

Table 2 reports an unlabelled tooth at lab `AA-114469` with 6989 ± 45 14C BP and 5976–5764 cal BCE. Its context does not identify `OB20-01`. A web rendering of the [published article](https://doi.org/10.1038/s41562-021-01083-y) has also been observed with 5983–5751 cal BCE for that measurement; that rendering has not been captured as a governed source artifact. The source-to-specimen link and differing calibration must be resolved before assigning either interval to `OB20-01`. No site coordinates are supplied by these dates. The Obishir V site attribution comes separately from the paper reporting summary, page 3.

The retained [Supplementary Data A–D workbook](../../../../data/adna/governance/source_library/papers/10.1038-s41562-021-01083-y/supplementary/41562_2021_1083_MOESM4_ESM.xlsx), sheet `B - Zooms and peptide data`, has literal identifiers `DA-OBI-1518-20.1`, `DA-OBI-1518-20.6` and `DA-OBI-1518-21.4` in cells A39, A123 and A125. Descriptive columns B:I contain layer, layer depth, context, element, side, taphonomic notes, weathering and pathology notes. Those rows describe left upper permanent M3, left lower deciduous I3 and left lower deciduous P3/P4 respectively; their contexts are Square R8, Square R10/11 and Square R9. The layer-depth header supplies no unit, and present blank cells remain blank. These are three unmatched source-context candidates: the retained ENA records and examined publisher HTML, supplementary information and reporting-summary text establish no explicit crosswalk to the five governed ENA aliases. Matching numeric suffixes alone does not establish specimen identity. Identifiers ending `-20.4` or `-21.6` were not found in this sheet's identifier column; that finite nonmatch is not absence from every source. No expected-population, biological identity, date, coordinate or map decision changes.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native DNA specimen/publication/chronology scope and unsupported ecological or pollen extension.

**Supported claim.** The retained Obishir review distinguishes specimen-matched calibrated BCE intervals from uncalibrated radiocarbon measurements.

**Unsupported claim.** An unlabeled dated tooth is not OB20-01, and an article variant is not authority to overwrite the governed PDF.

**Actual verification performed.** Read the source-specific Table 2 interpretation and current animal chronology account; this is document correspondence review, with no calibration or new specimen join. Primary PDF Table2 and ENA independently bind AA-114607 to SAMEA8022724/OB20-04. The source-bound actual materializer and independent1475-owner comparison carry its stratigraphic caution into review/temporal comparison notes while preserving4650–4952BP and all other selected dates/classes. The public reader changes only this owner conflict/review notes; no calibration, specimen reassignment or map rebuild.

**Remaining input or review.** The undated aliases need specimen-owned dates; source warnings and the Capra species conflict need qualified resolution.

**Cause category.** Incomplete specimen linkage and mixed dating representations.

**Consequence.** A site-level date cannot fill an undated sample or override the goat/sheep refusal.

**Precise next acceptance route.** Provide an unambiguous specimen-to-lab/date join and qualified calibration/species decision before changing chronology eligibility.

**Negative or refused result.** OB20-01 and OB21-06 have no matched direct date; OB21-04 remains sheep-blocked; OB20-04 retains stratigraphic inconsistency.

**Matched denominator.** 5 archive accessions; 3 stated specimen-date matches include one Capra sample; calibrated BCE ranges and uncalibrated 14C BP remain distinct.

- [Retained qualification evidence: docs/report/animal_sample_chronology_review.json](../../animal_sample_chronology_review.json) (SHA-256 `019d1a03ae1f708fe0a04e68f4edaaccfec1b3de8b4b52d2a202093aa84e1714`).

- [Retained qualification evidence: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-sample-chronology.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-sample-chronology.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
