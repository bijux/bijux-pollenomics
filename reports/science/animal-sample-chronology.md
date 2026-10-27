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

## Palm143 sample row and sequencing treatments

The original supplement and methods in [Mohandesan et al., DOI
10.1111/1755-0998.12551](https://doi.org/10.1111/1755-0998.12551), retained with
the [primary PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5324683/),
now distinguish the author sample row from its technical treatments. Table S1,
first Word table, physical row 12, contains one `Palm143` sample/find row:
`Pa604/138`, excavation year `2002`, `Syria Palmyra`, and contextual age
`100 BCE- 300 CE`. This is one author row, without establishing one independent
biological individual or a new selected chronology. Its extraction/library
fields are `RH / +`, `DSL / +` and `MB`; the caption defines RH as the Rohland
extraction method and MB as MYbaits enrichment.

The retained official accession bridge distinguishes two sequencing treatments:

| BioSample | Experiment / run | Source title and alias |
| --- | --- | --- |
| `SAMN04631877` | `SRX1711548` / `SRR3400280` | `Palm143_DSL_Capture_se`; alias `Palm143` |
| `SAMN04631967` | `SRX1711558` / `SRR3400290` | `Palm143_DSL_SG_se`; alias `Palm143_II` |

Original Table S3 places `Palm143` in its MYbaits single-end section at physical
row 12 and its single-end shotgun section at row 105. Table S5 row 32 repeats
the shotgun context. These are method/result representations of the same author
label, without proving independent specimens. The retained SRA listing reports
324,015 spots for `SRX1711558`, matching the shotgun row's 324,015 raw reads;
the capture listing rounds its count to 1.9 million, so it supplies no second
exact count comparison. No sequence or genotype inference follows.

Table S1's `Whole genome shotgun sequencing (WGSS)` cell for `Palm143` is
physically present but empty. A direct XML check found no symbol or drawing
concealing text. Preserve this blank alongside the Table S3 shotgun entry;
neither is silently corrected from the other. The article's **Ancient DNA
extraction** methods explicitly describe two independent DNA extractions per
sample. Extraction independence is different from specimen independence, and
the reviewed originals do not assign these two accessions to particular
extracts or physical bones. Both identity refusals remain: do not automatically
collapse or independently count the BioSamples, select new dates or coordinates,
or change their map/admission posture.

The shared original source is `adna/pmc5324683/supplementary-files.zip`,
2,654,016 bytes, SHA-256
`53a13186de7bdee427adce5d88d06ad14614c84719e6790dc7d86fd205e4fc1f`.
Its `MEN-17-300-s001.docx` member was streamed in place, without materializing
the 170,976,839-byte file; its SHA-256 is
`28f4c7524b035e550b8e135176b7571aa67686eec9bc7a4db63a554d0534c5b9`.
Only `word/document.xml` was parsed; both streamed members completed their ZIP
CRC checks. Original bytes remained unchanged. The retained primary HTML names
CC BY 4.0 for the article; this factual context does not infer a blanket
attachment redistribution grant. No original attachment or image is copied
into this account.

The source read terminated with exit zero in 0.42 s process wall time and
75,464,704 bytes peak RSS. A separate cell-layout check terminated with exit
zero in 0.29 s and 81,756,160 bytes peak RSS. Both stayed within the declared
120 s / 512 MiB / 4 MiB text bounds. Scoped methods/table text, literal cell
states, source identities and actual tool/resource facts remain under
`artifacts/adna/palm143-source/`. These checks establish source context;
the accession-to-extraction-to-bone crosswalk remains the precise missing fact.

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
coordinates. These labels do not establish a shared radiocarbon epoch or a selected age.
The separate alternative accounting below evaluates the signed-calendar
coordinates using the source-defined 2017 reference; it does not convert R/S. Formula text and its stored cached value remain
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
The 54 rows with additional date values now have the separate arithmetic
accounting below; their presence does not turn the 191 blank rows into dated
observations.

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

## Source alternatives and selected-field discrepancies

The unmet question after retaining literal cells was whether the alternative
calendar fields can be reconciled on a source-defined reference, rather than
waiting for an unspecified chronology review. The primary article's
[Experimental Model and Subject Details](https://pmc.ncbi.nlm.nih.gov/articles/PMC6547883/)
defines specimen-name ages as years ago from **2017**, with mixed direct
radiocarbon and archaeological dating. Its radiocarbon methods identify
OxCalOnline and IntCal13; Table S1 supplies the calibrated alternatives.
This supports the following explicitly scoped arithmetic without a new source
request or a new calibration.

The public provenance consumer now adds a separate
`source_chronology_alternatives` sibling for the 245 horse owners. The existing
literal packet, including `date_conversion_performed=false`, remains unchanged.
The new sibling uses T/U as the source's signed unmodelled BC/AD coordinates,
V as source interval coverage, W as the supplied average, and X as the supplied
signed offset. It checks **W − (T + U)/2** and **X − (W − 2017)** independently.
It also derives the affine elapsed coordinate **[2017 − U, 2017 − T]**, with
midpoint **2017 − W**, keeping the sign of source X distinct. These are
coordinates of the source's signed numbers: the source does not define a civil
calendar year-zero convention, so they are not elapsed physical durations across
year zero or newly admitted calibrated-BP intervals. W equals the endpoint
midpoint on all 54 rows; no posterior-mean interpretation is inferred. V supplies neither a Gaussian sigma nor an uncertainty
law for propagation. R/S remain uninterpreted; their missingness cannot refuse
otherwise valid T–X arithmetic. No formula is evaluated.

At committed source **`d9a4ea9a3653cd6c07a0f924e1259b5ccac8eede`**, the actual
1,475-row public consumer returned **245** alternative packets and no new
alternative field on the other **1,230** rows. All **54** populated alternatives
have zero midpoint and signed-offset residuals. All **191** rows with seven
physically present blank R–X cells remain explicitly refused. No alternative
is filled from D, the sample-name age, R/S or another specimen.

For the 54 populated alternatives, comparing unambiguous numeric D literals
with the derived elapsed-coordinate midpoint gives:

| D comparison | Owners |
| --- | ---: |
| Equal numeric coordinate | 18 |
| D minus derived midpoint = −0.5 | 31 |
| D minus derived midpoint = +0.5 | 2 |
| D minus derived midpoint = +2.5 | 1 |
| D minus derived midpoint = −1,752.5 | 1 |
| Non-numeric range, not compared | 1 |

The +2.5 case is `CGG_1_020484` at physical row 119: D is `4058`, while the
alternative midpoint is `4055.5`. The −1,752.5 case is `CGG_1_018577` at row
282: D is `1143`, while the alternative midpoint is `2895.5`. The range
`3039-3130` for `CGG_1_018080` at row 233 remains text and is not collapsed to
a date. These are source-coordinate disagreements, not a verdict about which
date is correct. Half-year differences are retained without assigning a
rounding rule. Neither agreement nor disagreement establishes D's dating
basis, scale, precision or selection authority.

The same paper preserves corresponding distinctions. Its Experimental Model
and Subject Details → Spain paragraph calls the specimen
`ElAcequion_Spain38_4055`, while Method Details → DNA extraction and genome
sequencing calls it `ElAcequion_Spain38_4058`. Results → Influence of Persian
Lines Post C7th–C9th describes `Zhanaturmus_Issyk1_1143` as a ninth-century
Kazakhstan horse, which is distinct from that row's T–X alternative coordinate.
These statements are from the same publication and retain their shared source
dependence. They were checked in the retained
[primary article capture](../../data/adna/governance/source_library/papers/10.1016-j.cell.2019.03.049/article.html.gz)
for table rows 119 and 282. They make the discrepancies useful curation
evidence without resolving which field should supply a selected date. We
retain all of them without repairing the table or relabeling a specimen.

All **1,475** earlier packets equal the retained prior native result after
removing only the added alternative sibling, including the entire literal
source context. All **1,475** selected records also equal the governed project
snapshots after removing the two optional siblings. No selected age, sample
membership, coordinate, map, admission or rights decision changes.

The actual direct `/usr/bin/time -l .venv/bin/python -B -` command called
`build_sample_chronology_provenance_rows(Path("data"))`, performed those two
population comparisons and serialized a JSON list. Owned session **80537**
terminated with exit zero in **3.87 s**, peak RSS **205,062,144 bytes**. The
6,809,994-byte private packet artifact and 7,432-byte summary are retained at
`artifacts/animal-source-chronology/source-alternatives/{provenance,summary}.json`.
They fit the predeclared 180-second, 512-MiB resident-memory, 16,000,000-byte
packet and 100,000-byte summary bounds. The exact inline command and terminal
facts are in the adjacent `execution.json`, `stdout.txt` and `stderr.txt`.
The earlier session **39005** exited one in 3.68 s because the inline comparison
expected the previous artifact to be a list rather than its actual `rows`
wrapper. Only that observer shape assumption was corrected for the same-source
retry; no scientific source, calculation, population or tolerance changed.
Its failed command and resources remain in `failed-execution.json`.

An independent original-ZIP/XML observer used DOM traversal and exact rational
arithmetic, rather than the producer's cell reader and Decimal calculations.
At observer commit **`547d24718cca48d8deaa2e00b0441d3b2418139f`**, owned
session **75988** passed **three tests in 2.91 s**, with **3.41 s** process
wall time and **197,050,368 bytes** peak RSS, without skips. Two checks compare
the saved result with all 245 native alternatives and all 1,475 prior packets;
the existing literal observer separately reopens the original workbook and
recomputes the public API, checking all 1,960 date cells and all selected
snapshot fields. Configured Ruff and strict types passed for the observer.
Its recorded command was:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /usr/bin/time -l .venv/bin/python -B -m pytest -c configs/pytest.ini \
  packages/bijux-pollenomics/tests/unit/adna/projects/sample_master/tables/test_horse_chronology_alternative_result.py \
  packages/bijux-pollenomics/tests/unit/adna/projects/sample_master/tables/test_horse_source_field_result.py \
  --basetemp=artifacts/animal-source-chronology/alternatives-independent-observer/pytest \
  --timeout=180 -q
```

The observer's stdout/stderr remain in that owning artifact directory. Use a
fresh basetemp for a new invocation to retain the completed run's evidence.

Before commit, **34** focused alternative, literal-field and adapter checks
passed, with configured Ruff lint/format and strict types for all three changed
Python paths. The initial formatting check and unavailable optional HTML parser
were corrected using the configured formatter and standard-library HTMLParser;
no dependency was installed. This unit adds source-specific arithmetic and
explicit conflicts to the maintained consumer, beyond the earlier literal scan.

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

**Supported claim.** All 260 horse source identities and native elapsed-age tokens are preserved; 250 unsupported BP intervals are refused. The PRJEB31613 provenance consumer additionally preserves 1,960 labeled source-date cells for 245 owners and separately accounts for 54 signed-calendar alternatives against the source-defined 2017 reference: 18 equal numeric D coordinates, 35 different and one range left uncomputed. All 191 blank alternatives and every selected chronology remain unchanged. Generic direct radiocarbon evidence and precision remain refused; Palm143 identity refusal is retained. Separate Galician curation exposes eleven sample-owned supplement rows as 110 literal typed cells, with radiocarbon, calibrated-BP, calendar and locality fields kept distinct. Palm143 source curation distinguishes one author Table S1 sample/find row from capture and shotgun technical representations across two BioSamples, without selecting physical specimen identity.

**Unsupported claim.** A universal 67-year shift, calibrated BP, or per-row direct radiocarbon support from the imported mixed elapsed-age field; distinct physical identity for both Palm143 BioSamples; ecological events.

**Actual verification performed.** The alternative consumer ran at d9a4ea9a3653cd6c07a0f924e1259b5ccac8eede, session 80537 exit zero: all 54 source midpoint/offset equations hold, all 245 owners and 191 blank refusals reconcile, and all 1,475 previous packets and selected fields remain unchanged. The independent DOM/rational saved-result and original literal observers passed three tests at 547d24718cca48d8deaa2e00b0441d3b2418139f, session 75988, confirming all alternative/source counts and unchanged packets. The producer’s initial wrapper-comparison failure and same-source correction are retained above. The horse source-field consumer and independent raw-XML test ran at a1f04506dd1a26ea63cda0f2c3526814629fc995, both exit zero: all 245 source owners/1,960 date cells agree, with 1,475 old provenance packets unchanged and no new field on the other 1,230. No map or selected-age writer was rerun for this source-field result. Earlier actual owned source and dependent-data consumers, three qualified map surfaces and five paired final/public/governance owners returned; baseline drift was zero and immutable source/country/map inputs were preserved. World/Europe actual returned predecessor stages were retained with the CSS-only renderer; Nordic was freshly published. The index did not rerun. The Galician optional consumer ran at 85de3133f, exit 0 in 2.30 s, producing a 19905-byte context table. An independent DOM source check confirms all 110 cells, original header/unit/type/style/value/blank/formula states and exact eleven crosswalk rows.Fifty controlled tests plus the native default-writer exact-byte test pass, with configured lint/types. Original default report/species CSV remain unchanged. Original nested DOCX was streamed in place without materializing its 170976839 bytes; only document.xml and retained primary HTML were read. Independent literal-layout checking confirms the ten non-sequence header/target cells and four author-label occurrences, including a physically present empty WGSS cell. Original ZIP identity and both identity refusals remain unchanged. Actual reading .42 s/RSS75464704 B; separate layout check .29 s/RSS81756160 B; the actual report render and 24 reader controls pass.

**Remaining input or review.** The Cell 2019 native selected Age (years ago) field still has no established field-specific epoch and scale mapping; the separate T–X alternative arithmetic is now source-bound to 2017 without adopting a civil year-zero convention; a mixed project dating basis cannot classify every row as direct radiocarbon. Two Palm143 BioSamples also retain unresolved physical specimen identity. Resolver: Horse source chronology reviewer and SRP073444 specimen/source owner Reopen when: Source-backed field epoch and scale or independently dated per-row evidence permits horse chronology; citable accession-to-physical-specimen evidence resolves Palm143.

**Cause category.** data|assumption

**Consequence.** Source chronology nodes, locality features and mapped samples have distinct admission contracts. Elapsed-age text cannot become BP or direct radiocarbon support, and accession labels cannot establish independent specimens.

**Precise next acceptance route.** Resolve the selected D field meaning, per-row dating evidence and source conflicts before re-admitting horse chronology; preserve the now-accounted alternative coordinates as distinct source context. Resolve Palm143 physical specimen identity from citable source evidence before revising its source-sample publication decision. Use the source treatment distinction now; obtain the specific accession-to-extraction-to-physical-bone crosswalk before changing Palm143 identity or dependency grouping, without requesting the already retained supplement again.

**Negative or refused result.** 250 previously inferred BP intervals are refused; all 260 selected horse dating-evidence and precision classifications remain unresolved. Among the 245 linked source-field rows, 191 have blank R–X cells and eight have literal `-` in D; all 54 populated alternatives are arithmetically consistent, but 35 numeric D values differ from their alternative midpoints and one range is not compared. No selected chronology is established by this accounting. The global refusal waterfall has 7 identity, 789 chronology and 356 coordinate refusals. Both Palm143 accessions remain identity-refused. Galician sample SAMN18106837 keeps modern-carbon text, a blank calibrated-BP cell and last-60-years calendar text; its label establishes neither 60 BP nor Cobas locality. All eleven retain unresolved site/date and refused atlas-point posture. Table S1 WGSS is blank while Table S3 separately includes a shotgun row. The two accession titles distinguish capture/shotgun treatment, and extraction independence does not establish specimen independence. Exact accession-to-extraction-to-bone binding remains absent; neither collapse nor independent biological counting is adopted.

**Matched denominator.** 1,475 source rows = 323 temporal nodes + 1,152 refusals; 13 temporal nodes each in Europe-plus/Nordic. Separate normalized foundation: 1,468 rows; locality atlas: 165 features/322 mapped samples; 12 Nordic mapped IDs. Separate Galician context:11 BioSamples versus 18 paper specimens;110 exact cells: 109 shared strings, one present blank, zero formulas. Separate Palm143 context: two BioSamples/experiment-run pairs, one Table S1 sample/find row, two Table S3 treatment rows and one Table S5 repeat; four author-label occurrences are not four specimens.

Retained evidence: [data/adna/governance/source_library/projects/PRJEB31613/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB31613/sample_master.json), [data/adna/governance/source_library/projects/PRJEB19970/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB19970/sample_master.json), [data/adna/governance/source_library/projects/SRP073444/sample_master.json](../../data/adna/governance/source_library/projects/SRP073444/sample_master.json), [docs/report/animal_sample_chronology_review.json](../../docs/report/animal_sample_chronology_review.json), [reports/science/source-cohorts/galician-sample-context.csv](source-cohorts/galician-sample-context.csv), [artifacts/animal-source-chronology/native-source-fields/summary.json](../../artifacts/animal-source-chronology/native-source-fields/summary.json), [artifacts/animal-source-chronology/source-alternatives/summary.json](../../artifacts/animal-source-chronology/source-alternatives/summary.json), [data/adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html.gz](../../data/adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html.gz).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
