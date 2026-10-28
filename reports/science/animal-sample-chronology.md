# Why source animal ages and specimen identities remain refused

## Our decision

The horse tables in [Fages et al. (2019)](https://doi.org/10.1016/j.cell.2019.03.049)
provide an `Age (years ago)` field, which we preserve as source text. We refuse
its conversion to a BP interval until the field-specific epoch and age scale
are established. The article relates specimen-name ages to 2017, using direct
radiocarbon dates or archaeological context. Table S1 also contains distinct
radiocarbon columns, an explicit `(from 2017)` header, and IntCal13 unmodelled
BC/AD columns. These different fields require separate interpretation; we do
not apply a universal 67-year shift or claim a new radiocarbon calibration.

A mixed project-level dating description does not establish that every native
elapsed-age value is a direct radiocarbon date. For example, `Batagai_5155` has
an elapsed-age value of 5155 while the retained Table S1 radiocarbon and
calibrated-date cells on its row are blank. The imported elapsed field retains
unresolved dating evidence and precision. Independently documented per-row
evidence remains distinct from the refused conversion.

We also treat two `SRP073444` BioSamples, `SAMN04631877` and `SAMN04631967`, as
unresolved physical specimen identities. Their [governed sample rows](../../data/adna/governance/source_library/projects/SRP073444/sample_master.json)
have distinct accessions but share the paper label `Palm143`. We refuse their
sample identity before evaluating whether their coordinates are mappable. A
nearby or missing coordinate cannot establish that they are independent
specimens.

## What we ran and observed

The source correction retains all **260** rows from the [245-row horse time
series](../../data/adna/governance/source_library/projects/PRJEB31613/sample_master.json)
and [15-row comparative panel](../../data/adna/governance/source_library/projects/PRJEB19970/sample_master.json).
It removes **250** previously inferred BP intervals: 237 and 13 respectively.
Native identifiers, source tokens and unrelated sample fields are preserved.
The separate Nature 2021 source has an explicit `AgeEstimate (BP)` field; its
248 source rows and chronology records remain unchanged.

Across **1,475** source rows, the corrected chronology display admits **323**
nodes and refuses **1,152** rows. The exclusive refusal waterfall contains
**7** unresolved sample identities, **789** non-comparable chronologies and
**356** unmappable coordinates. The earlier display admitted 557 nodes.
Removing unsupported intervals removes **234** world features; the other
**16** affected rows were already refused for coordinates and now fail at the
earlier chronology check. The two `Palm143` identity refusals are unchanged.

The [world](../../docs/report/world/world_animal_sample_chronology_context.json)
display includes all 323 admitted nodes. [Europe-plus](../../docs/report/regions/europe-plus/europe-plus_animal_sample_chronology_context.json)
and [Nordic](../../docs/report/regions/nordic/nordic_animal_sample_chronology_context.json)
each include **13**, after removing one unsupported horse chronology feature.
These regional counts are projections of the same global source corpus; the
1,152 refusal rows describe that corpus rather than a new regional denominator.

The [source replay regression](../../packages/bijux-pollenomics/tests/unit/reporting/adna/sample_chronology_context/test_repository_data.py)
checks exact source denominators, identity sets, input bytes and the chronology
publication contract through all three map surfaces. The owning source and
map writers regenerate provenance, source-site labels, horse normalization,
map contracts and hashed display chunks together. The existing bundle dates
remain publication provenance, not a new source age or source capture date.

## What the result permits

These layers provide source-sample chronology context for display. They do
not establish ecological events, independently measured vegetation, a
pollen-core chronology or a spatially precise ancient animal distribution.
Re-admitting the horse elapsed-age field requires a supported relation between
its native field, epoch and scale. Re-admitting either shared `Palm143`
accession requires source evidence that resolves its physical specimen identity.
