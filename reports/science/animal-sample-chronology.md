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

## Labeled horse source-date fields

The maintained sample chronology provenance consumer additionally exposes
`source_chronology_fields` for the PRJEB31613 horse rows. This is source context,
separate from the selected chronology. It retains worksheet column D and R–X,
the original four header rows at those columns, physical row and cell references,
sample and registration labels, and the current workbook byte identity. Every
native horse row must match exactly one existing sample owner and physical row.
Other source species remain explicitly counted outside that population.

The literal header coordinates preserve `14C age(BP)` at R3 and `(from 2017)`
at R4, alongside the IntCal13 and unmodelled BC/AD labels at their own source
coordinates. These labels do not establish a shared epoch, a signed-calendar
conversion or a selected age. Formula text and its stored cached value remain
separate; the reader does not evaluate formulas. Numeric zero, a literal
placeholder, a physically present blank cell and an absent cell remain distinct.
Per-column cell-state and formula counts cover the complete linked population.
Missing optional source bytes produce an explicit refusal with unknown counts;
inconsistent source ownership or representations are refused.

The existing workbook metadata describes recovery from a DOI-keyed local
supplement stash and supplies no historical source digest. The new current-byte
identity cannot authenticate that acquisition history or establish reuse rights.
This evidence does not revise the selected ages, chronology classifications,
coordinates, sample membership, maps or scientific admission.

### Observed source-field population

The actual public provenance consumer ran at committed source
`a1f04506dd1a26ea63cda0f2c3526814629fc995`. Session **17022** terminated
with exit zero in **2.356145625 s**, with peak resident memory **189,497,344
bytes**. It returned 1,475 provenance packets: all 245 PRJEB31613 owners have
the additional source context, and the other 1,230 have no added field. Every
previous field in all 1,475 packets equals the existing governed provenance
snapshot after removing only `source_chronology_fields`.

The consumed workbook is the retained
[`1-s2.0-S0092867419303848-mmc1.xlsx`](../../data/adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/supplementary/1-s2.0-S0092867419303848-mmc1.xlsx),
81,103 bytes, SHA-256
`e37e1720c160cc0d7eaa4037ece22c1d9f8812f0cb31635647f26ca93137dd29`.
Its worksheet contains 280 physical rows after the four header rows: 245
horse owners, 27 mule, three ass, three hemione and two rows without a sample
label. These are worksheet rows, not 280 independent biological specimens.
The 245 horse owner IDs, labels and physical row locators reconcile one to one.

| Source field population | Observed result |
| --- | --- |
| D and R–X cells linked to horse owners | 1,960 cells, including zero absent cells |
| D cells | 245 populated: 147 numeric XML values and 98 shared strings |
| D shared-string placeholders | Eight literal `-` values; selected date provenance remains empty/unresolved |
| Each R–X column | 54 populated and 191 physically present blank cells |
| R–X row patterns | 54 complete seven-value rows and 191 complete seven-blank rows |
| Source formula evidence | One D formula with its stored cache; no R–X formulas |
| Repeated header and identity records in the packets | 7,840 header records from 32 source header cells; 735 identity records |

For example, `D72` retains the formula `4625+67` and stored value `4692`
without evaluating the formula or adopting its epoch for other rows. At row
282, D contains `1143` while X contains `-2895.5`; neither value is selected
to repair the other. The Uppsala row retains its source age-range text while
R–X remain blank. Field disagreement and missingness survive this preparation.
The 54 rows with additional date values can now receive field-specific review;
their presence does not turn the 191 blank rows into dated observations.

The recorded native command used `/usr/bin/time -l .venv/bin/python -B -c`
and the maintained public call:

```python
from pathlib import Path
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_sample_chronology_provenance_rows,
)

rows = build_sample_chronology_provenance_rows(Path("data"))
```

The complete inline command and terminal status are retained in
`artifacts/animal-source-chronology/execution.json`. The existing public API
is the producer; no additional launcher is required. Its compact private
`native-source-fields/provenance.json` is **6,539,545 bytes**, below the
predeclared 16,000,000-byte limit. The adjacent `summary.json` is below its
100,000-byte limit, and the process remained within the 180-second bound.
These artifacts stay outside Git; no workbook or full packet copy is added
to the public report.

An independent reader traversed the original ZIP/XML directly and compared
every linked date, header and identity record, source type/style, raw and
resolved value, formula/cache, blank/missing state, physical owner and summary
count. It also checked every old provenance field. Its committed-source
session **99057** passed one test in **2.45 s** (2.84 s process wall time,
peak resident memory 172,408,832 bytes). The maintained command is:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /usr/bin/time -l .venv/bin/python -B -m pytest -c configs/pytest.ini \
  packages/bijux-pollenomics/tests/unit/adna/projects/sample_master/tables/test_horse_source_field_result.py \
  --basetemp=artifacts/physical-core/horse-source-fields/committed-public-observer -q
```

Before commit, 27 focused checks and two subtests passed, together with
configured Ruff formatting/lint and strict types for the six changed Python
paths; the independent observer also passed strict types. Earlier working-tree
checks exposed eight owners with empty selected-date provenance, so the added
context now uses their unchanged master identity lineage. The existing
220-line adapter guard required a separate horse source-field package; the
guard was preserved. The independent test's initial blank-registration
fallback was corrected in the observer. An initial test-style lint finding
was also corrected. Those unsuccessful checks remain distinct from the
successful committed-source runs; their local logs are retained.

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

## Literal Galician sample context

The [Galician cell table](source-cohorts/galician-sample-context.csv) joins the
existing eleven-BioSample/specimen crosswalk to 110 original supplement cells
in rows 16–25 and 27. The dating table contains eighteen paper specimens; that
is a separate population from the eleven sequenced BioSamples. Each exported
cell retains its worksheet part, native coordinate, header and units, original
type/style attributes, stored value, resolved text and formula/cache presence.
Headers and strings are not trimmed, dates are not converted and formulas are
not evaluated. All 109 populated cells are shared strings; `G27` is a present
blank cell, distinct from both a missing cell and numeric zero. No selected cell
contains a formula.

For `SAMN18106837`, the label `Bt_CO_(60BP)` must not supply locality or age.
The exact row for specimen `UK-LU-01` reports `Chan do Lindeiro (entrance)`,
`100% modern C` under `Age 14C BP`, a blank `Age cal BP (2-sigma)` cell and
`last 60 years` under `Age cal BC/AD `. These source statements remain separate;
we infer neither 60 BP nor a Cobas site from the label. Other rows likewise keep
radiocarbon, calibrated-BP, calendar and contextual fields apart.

The opted-in maintained consumer ran at `85de3133f` with exit zero in 2.30 s.
An independent DOM reader of the original workbook ZIP/XML checked all 110
cells, header/row identities, types, styles, values and blank/formula states
against the exported table. Fifty controlled tests and the separate native
original-writer test pass, with configured lint, formatting and strict types.
The [original species report and CSV](../../docs/report/source-relations/dna-scope/galician-cattle-samples/README.md)
remain byte-identical under the default command. The opted-in report adds only
a literal-context summary; its species CSV is also unchanged. All eleven
sample-master site, chronology and atlas-point decisions remain unresolved or
refused. This makes original context reviewable; it does not approve a date,
site assignment, project-paper promotion, source permission or scientific use.

Reproduce the optional table from the repository root with an absent output:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.adna.galician_sample_review \
  --repository "$PWD" \
  --output "$PWD/artifacts/galician-sample-context" --literal-context
```

## What the result permits

These layers provide source-sample chronology context for display. They do
not establish ecological events, independently measured vegetation, a
pollen-core chronology or a spatially precise ancient animal distribution.
Re-admitting the horse elapsed-age field requires a supported relation between
its native field, epoch and scale. Re-admitting either shared `Palm143`
accession requires source evidence that resolves its physical specimen identity.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** All 260 horse source identities and native elapsed-age tokens are preserved; 250 unsupported BP intervals are refused. The PRJEB31613 provenance consumer additionally preserves 1,960 labeled source-date cells for 245 owners, without changing any selected chronology. Generic direct radiocarbon evidence and precision remain refused; Palm143 identity refusal is retained. Separate Galician curation exposes eleven sample-owned supplement rows as 110 literal typed cells, with radiocarbon, calibrated-BP, calendar and locality fields kept distinct.

**Unsupported claim.** A universal 67-year shift, calibrated BP, or per-row direct radiocarbon support from the imported mixed elapsed-age field; distinct physical identity for both Palm143 BioSamples; ecological events.

**Actual verification performed.** The horse source-field consumer and independent raw-XML test ran at a1f04506dd1a26ea63cda0f2c3526814629fc995, both exit zero: all 245 source owners/1,960 date cells agree, with 1,475 old provenance packets unchanged and no new field on the other 1,230. No map or selected-age writer was rerun for this source-field result. Earlier actual owned source and dependent-data consumers, three qualified map surfaces and five paired final/public/governance owners returned; baseline drift was zero and immutable source/country/map inputs were preserved. World/Europe actual returned predecessor stages were retained with the CSS-only renderer; Nordic was freshly published. The index did not rerun. The Galician optional consumer ran at 85de3133f, exit 0 in 2.30 s, producing a 19905-byte context table. An independent DOM source check confirms all 110 cells, original header/unit/type/style/value/blank/formula states and exact eleven crosswalk rows.Fifty controlled tests plus the native default-writer exact-byte test pass, with configured lint/types. Original default report/species CSV remain unchanged.

**Remaining input or review.** The Cell 2019 native Age (years ago) field has no established field-specific epoch and scale mapping; a mixed project dating basis cannot classify every row as direct radiocarbon. Two Palm143 BioSamples also retain unresolved physical specimen identity. Resolver: Horse source chronology reviewer and SRP073444 specimen/source owner Reopen when: Source-backed field epoch and scale or independently dated per-row evidence permits horse chronology; citable accession-to-physical-specimen evidence resolves Palm143.

**Cause category.** data|assumption

**Consequence.** Source chronology nodes, locality features and mapped samples have distinct admission contracts. Elapsed-age text cannot become BP or direct radiocarbon support, and accession labels cannot establish independent specimens.

**Precise next acceptance route.** Bind source-field epoch and scale and per-row date evidence before re-admitting horse chronology. Resolve Palm143 physical specimen identity from citable source evidence before revising its source-sample publication decision.

**Negative or refused result.** 250 previously inferred BP intervals are refused; all 260 selected horse dating-evidence and precision classifications remain unresolved. Among the 245 newly linked source-field rows, 191 have blank R–X cells and eight have literal `-` in D; additional native values on 54 rows do not establish selected chronology. The global refusal waterfall has 7 identity, 789 chronology and 356 coordinate refusals. Both Palm143 accessions remain identity-refused. Galician sample SAMN18106837 keeps modern-carbon text, a blank calibrated-BP cell and last-60-years calendar text; its label establishes neither 60 BP nor Cobas locality. All eleven retain unresolved site/date and refused atlas-point posture.

**Matched denominator.** 1,475 source rows = 323 temporal nodes + 1,152 refusals; 13 temporal nodes each in Europe-plus/Nordic. Separate normalized foundation: 1,468 rows; locality atlas: 165 features/322 mapped samples; 12 Nordic mapped IDs. Separate Galician context:11 BioSamples versus 18 paper specimens;110 exact cells: 109 shared strings, one present blank, zero formulas.

Retained evidence: [data/adna/governance/source_library/projects/PRJEB31613/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB31613/sample_master.json), [data/adna/governance/source_library/projects/PRJEB19970/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB19970/sample_master.json), [data/adna/governance/source_library/projects/SRP073444/sample_master.json](../../data/adna/governance/source_library/projects/SRP073444/sample_master.json), [docs/report/animal_sample_chronology_review.json](../../docs/report/animal_sample_chronology_review.json), [reports/science/source-cohorts/galician-sample-context.csv](source-cohorts/galician-sample-context.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
