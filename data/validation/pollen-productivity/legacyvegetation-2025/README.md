# LegacyVegetation pollen-productivity reference

Schild, L., Ewald, P., Li, C., Hébert, R., Laepple, T. and Herzschuh, U. (2025),
*LegacyVegetation: Northern Hemisphere reconstruction of past plant cover and
total tree cover from pollen archives of the last 14 kyr*.
[Paper and appendices](https://doi.org/10.5194/essd-17-2007-2025),
licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

This reference preserves both published parameter workbooks and their transport
receipts under [originals/](originals/). [source.json](source.json) records exact
hashes, source column mappings, coverage and unresolved discrepancies.

| Extraction | Contents |
| --- | --- |
| [original-study-estimates.csv](original-study-estimates.csv) | All 369 original estimate rows; uncertainty labelled SE |
| [synthesized-estimates.csv](synthesized-estimates.csv) | All 131 source rows for each of four regions; uncertainty labelled SD |

Every field retains its original cell reference. Numeric strings, taxonomic
levels, blank cells and en dashes remain unchanged. These tables extend the
[2020 reference](../wieczorek-herzschuh-2020/README.md); overlapping studies do not
become independent evidence.

## Source limitations

Two distinct `Sapindales` rows occur at worksheet rows 123 and 127. Both remain
in the extraction. Selecting by taxon name alone would be ambiguous. The exact
workbook contains 61 nonmissing European RPP rows and 93 Asian rows; the paper's
parameter-count prose reports 69 and 59 respectively. Their count definitions
remain unresolved.

European Ulmus productivity and uncertainty remain missing. Its hemispheric
values do not establish Swedish applicability. Table A1's SE and Table B1's SD
remain separate source labels; no conversion, covariance or between-study
interpretation is supplied here. The captured synthesis labels fall speed `vg`
without a unit; unit qualification remains outstanding.

This intake supplies parameter references for review. It does not replace an
existing model profile, recompute results, admit a physical basin or provide
independent measured vegetation validation. Missing parameter markers never
receive the negative-LOVE clipping rule.
