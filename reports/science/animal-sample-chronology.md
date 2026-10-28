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

## Obishir extraction and deposited-sample populations

PRJEB41594's expected biological population remains **unknown** after reading
the retained primary sources. The [Obishir paper](https://doi.org/10.1038/s41562-021-01083-y)
assigns shotgun raw files to that project in its final Data Availability section,
without specifying a closed project sample count. Its Reporting Summary page 2
selects six best-preserved specimens for genomic sequencing; page 3 describes
DNA extraction from six teeth, then five samples advanced to deep shotgun
sequencing. These are distinct analysis-stage populations. The summary's own
accession statement still contains an upload placeholder and cannot be cited
as an explicit five-sample project declaration.

The retained complete ENA run report has five runs, five experiments and five
BioSample aliases, but equality of these captured counts does not establish the
paper's expected biological denominator or independent individuals. All five
aliases match their original XML: OB20-01, OB20-06, OB21-04, OB21-06 and OB20-04.
Four retain native Ovis aries identity; OB21-04 / SAMEA8022722 retains Capra
hircus and its project-species mismatch. Supplementary Appendix F / Table 7
also identifies that Capra specimen. We do not call these five sheep or infer
the identity, failure, duplication or disposition of the additional selected
entry from the difference between six and five.

The [project master](../../data/adna/governance/source_library/projects/PRJEB41594/sample_master.json)
now records `source_population_unresolved`, the exact source-stage distinction
and Reporting Summary locator. Expected and unresolved counts remain null;
the five recovered/final records, all specimen fields, dates, coordinates and
the goat mismatch remain unchanged. Reopening requires a source-owned
specimen-to-analysis-stage crosswalk and a closed project submission roster.
Archive aliases, library counts and the Reporting Summary's Obishir site/permit
statement alone do not supply that evidence.

At committed source `8fa209201bb67906699a9ee02112ee92f0059ec7`, the maintained
one-project consumer and exact header/row comparison passed in 2.07 process
seconds with 78,331,904 B peak process RSS, within 60 s / 512 MiB / 8 MiB.
All 6,126 frozen source/input files and HEAD/index remain unchanged; only
status, provenance and source-locator headers differ. Two existing source-native
taxonomy controls, scoped lint/format and strict types pass. Independent original
page/ENA review agrees with the unresolved population decision. The initial
comparison failed because its wrapper expected `schema_version` inside the
native `as_dict`; the corrected wrapper uses the existing materializer envelope.
That failure remains preserved, with no source, data or scientific criterion
change. Both attempts and the final small product stay under
`artifacts/root/prjeb41594-population/`. No all-project materializer, chronology
census, model, atlas or source acquisition ran; aggregate intake/yield views
were not regenerated. Earlier Obishir dating-caution results remain unchanged.

## Bovine source panels and captured project populations

The [Nature source for PRJEB75467](https://doi.org/10.1038/s41586-024-08112-6)
explicitly declares **50 new samples** in its supplement, physical page 3
(printed page 2). Supplementary Data 1, cells A2:AB51, has 50 populated unique
Analysis IDs. Its literal Species column contains 41 Bos primigenius, eight
Bos taurus and one Bos admixed labels. Final Data Availability assigns new
reads and alignment files to PRJEB75467, separately from previously published
ancient and modern comparison data. This supports a published new-sample
denominator of 50; it does not establish 50 independent individuals, 50 aurochs
or a reviewed taxonomic change to the existing archive records.

The retained project snapshot contains **664 runs / 44 BioSamples**. The
[current master](../../data/adna/governance/source_library/projects/PRJEB75467/sample_master.json)
has 45 rows, including provisional supplement-only Fre1, and 44 records marked
final under the existing archive-identity rule. Its expected count is now 50.
The maintained counter reports six unresolved as **50 expected minus 44 final
archive-identity rows**, not five from subtracting the 45-row union. That is an
administrative balance, not six authenticated missing biological individuals.

Six source IDs lack exact captured filename stems: Fife1, Fre1, Narym1, Padova2,
Shauke8b and Var3. There is also a separate alias ambiguity: SAMEA115574406
contains both Borly4a and Borlya filenames, while SAMEA115574408 also contains
Borlya. We preserve every original row and do not turn those filenames into a
clean one-to-one specimen crosswalk. The supplement restricts the eight named
ASIAPAST samples BZL1, BZL2, NVL1, NVL3, KOL9, KOL10, ROS001 and ROS002 to
non-commercial use. This source-count curation grants no additional data-use
permission or genetic-analysis admission.

The separate [Science supplement for PRJEB31621](https://doi.org/10.1126/science.aav1002)
supports **66 ancient source IDs** in Table S1, pages 55–57. CPC98 is explicitly
previously published and enters the broader analysis in Table S2; Table S6,
page 68, separates nine modern genomes attributed to this study from 14 reused
genomes. The retained article HTML is a PubMed landing-page capture, not the
full Science article. Its 67-genome abstract is not a project deposition census.

The retained PRJEB31621 snapshot has **364 runs / 77 BioSamples**. Its
[78-row master](../../data/adna/governance/source_library/projects/PRJEB31621/sample_master.json)
is a union of 65 ancient-source/archive joins, twelve archive-only owners and
provisional supplement-only Men1. All 77 archive owners remain present.
Sixty ancient joins use literal filename prefixes and five use explicit library
aliases. The supplement identifies Men1 as `JK95-7-3-166-180('97)d`; it does not
bind that specimen to archive MV013 / SAMEA5577376 and its 24 runs. The nine
modern ERS identifiers likewise lack a retained ERS-to-SAMEA crosswalk and
closed project/reused-data inclusion decision. Expected and unresolved project
population therefore remain null, now with precise source-population provenance
rather than a generic weak-capture explanation. The 66, 67, 77 and 78 counts
describe different populations.

At committed source `8fe41f69d700a23eb30bdc6bd296d25fa399cdcb`, both maintained
project-master consumers and exact saved-row comparisons passed on their first
attempt in 2.15 process seconds, peak process RSS 89,784,320 B, within
60 s / 512 MiB / 8 MiB. All 6,126 frozen source/input files and HEAD/index stay
stable. PRJEB31621 changes three diagnostic headers; PRJEB75467 changes five
count/provenance headers. All 123 existing rows, provisional identities, native
taxa, dates, coordinates and source lineages remain exact. Two existing source
controls plus six project subtests and scoped lint/format/strict types pass.
Independent original PDF/workbook/ENA reviews distinguish these populations.
Products and guards remain under `artifacts/root/bovine-project-populations/`.
No global materializer, chronology census, model, map or source acquisition ran;
aggregate intake/yield views were not regenerated. Full named-project identity
recovery and biological/scientific acceptance remain open.

## Baltic sheep source population

The primary article for PRJEB59481 (DOI [10.1093/gbe/evae114](https://doi.org/10.1093/gbe/evae114)) explicitly assigns five new ancient individuals to this project. Its five Table 1 labels join five distinct official ENA BioSamples; comparison genomes reused by the paper are outside that project-owned population. The governed project master now records five expected and five recovered individuals, with zero unresolved count. This is identity-recovery accounting: all five sample rows, chronology/site/locality fields and five material-evidence conflicts remain unchanged. It establishes neither analytical admission nor a resolved material or chronology decision.

At committed consumer source `92b5042fc3dd327c7ea42445044610a9bb905b9c`, the one-project comparison passed in 0.805 seconds with 73,940,992 bytes peak RSS, within 60 seconds and 512 MiB. Exactly five header fields differ and all 18 guarded inputs were unchanged during execution. The comparison and proposed header are retained under `artifacts/adna/baltic-sheep-source-count/consumer-check/`. The earlier literal-source observer's incorrect label-order assumption and its corrected source check remain recorded separately. No all-project materializer ran; intake-dossier, yield and global completeness views were not regenerated.

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


## Obishir stratigraphic caution and locality coverage

A source warning must survive normalization and aggregation. Obishir V's retained
supplementary PDF, DOI `10.1038/s41562-021-01083-y`, page 11 Table 2, shades the
AA-114607 tooth date as inconsistent with stratigraphy. It reports context
`Obishir R10, Layer 2 Depth 4 (20.4)`, `4260* ±36` radiocarbon BP and
`3003–2701 cal BCE`, two sigma. The retained ENA record independently binds
`SAMEA8022724` to `OB20-04`, *Ovis aries*. The source warning was already in the
provenance excerpt but absent from the conflict/review fields used downstream.

The correction at `b20bce4a5` exposes that exact warning for its one specimen.
It preserves the published chronology, normalized interval 4650–4952 BP,
midpoint 4801, direct-date evidence class and source precision. It performs no
calibration, age substitution or species reassignment. The other four Obishir
owners remain unchanged; OB20-01 and OB21-06 remain undated. Twelve focused
controls, configured lint/format/strict types and independent PDF/ENA/code
review pass. The initial test-only typing failure remains retained.

The maintained chronology materializer then ran at committed `e9aff4a34`, with
only its output writers routed to
`artifacts/adna/obishir-chronology/materialization/`. It read canonical inputs
directly, with no input or numerical mocks. Process 11.02 s, RSS 262,864,896 bytes
and 37,254,885 generated bytes meet the prospective 180 s / 1.5 GiB / 96 MiB
bounds. All 260 products close: 240 are identical and 20 differ. The independent
comparison verifies all 1,475 owners and unchanged dates/classes/precision.
Eighteen paths carry the Obishir caution and related summaries. Two unrelated
horse-project provenance exports, and their corresponding global added keys,
were left in their previous installed epoch; the global Obishir update replaces
only its exact owner packet. No original capture or paper bytes changed.

The attention ledger grows from 928 to 929; the conflict ledger from zero to one.
The existing publication owner gate now blocks the nonempty conflict note.
This is a check of that owner's existing predicate, not a new whole-publication
qualification. The specimen has no coordinates, remains explicitly map-excluded,
and has no admitted source-chronology point; no atlas rebuild is warranted.
Numeric interval representation does not authenticate its stratigraphic context.

The successful independent comparison took 1.69 s, RSS 151,863,296 bytes, under
60 s / 512 MiB / 4 MiB. All 4,541 tracked Python files, 1,234 source-bank files,
HEAD and index remained stable through producer and observer. Its first attempt
stopped on an overly strict ordinary Markdown table-header check; the retained
successful readback permits only the two exact standard header/separator lines.
No product or scientific criterion changed. The independent result is
`artifacts/verification/obishir-chronology/independent-check.json`, 8,621 bytes,
SHA256 `8c0a74f0676588bf11e51e773c5a3df5585a112d23ae823dd37cfc0f8615f8ae`.
The existing 1,475-row public reader changes only this owner's conflict/review
notes; counts and authored Markdown remain exact. Its initial full-page versus
footer comparison failure and corrected body-only check are both retained.
Only the two genuinely dependent reader qualifications were refreshed.

A separate consumer correction at `d17e40e06` distinguishes a locality's coverage
hull from the dates of its samples. The project-locality constructor changes only
three aggregate labels to `locality_sample_coverage`,
`locality_sample_coverage_hull` and `display_coverage_only`. It preserves the
original aggregate text, endpoints, midpoint, missing values and refusal data.
Each sample retains its own date, evidence class, precision, provenance and
caution. A span covering samples does not supply observations throughout its
interior. Seven controls exercise disjoint intervals, missing/censored support,
source cautions, exact JSON/CSV ownership and the existing pig/aurochs consumers;
configured lint, formatting and strict types pass.

The actual sheep consumer at committed
`7053f6edcfb623cd1094fb6a8615d3376fa488f0` calls
`build_species_normalization_bundle("Ovis aries")` and the maintained sample and
locality JSON/CSV exporters. It retains 200 normalized samples, three original
identity-recovery refusals, nine localities and 200 locality memberships. Every
sample field is unchanged except OB20-04's conflict note. All nine locality
identities, order, membership, coordinates and numeric bounds remain exact;
only their three hull labels change. The locality JSON advances to its existing
v2 schema and supplies 200 separately owned chronology supports. The CSV adds
its four existing v2 support columns. These are temporal ownership records,
not 200 newly dated, independently validated or analytically admitted specimens.
Of the 200 source samples, 174 have numeric interval endpoints; missing or
unusable chronology remains explicit in the other 26.

The producer took 3.10 s, RSS 84,983,808 bytes, with 2,661,980 bytes before its
compact result, within the prospective 120 s / 1 GiB / 24 MiB envelope. The
independent literal checker took 1.67 s, RSS 30,556,160 bytes, within 60 s /
512 MiB / 4 MiB. It joins every support to its exact sample and checks all old
fields, three refusals, both CSV schemas and all four product identities.
All 4,542 Python files, 1,677 source inputs, HEAD and index remain stable.
Both actual runs pass on their first attempt, with no model, map or source
acquisition. Products remain in
`artifacts/adna/obishir-chronology/ovis-normalization/`; the 3,799-byte independent
result is `artifacts/verification/ovis-chronology-support/independent-check.json`,
SHA256 `a8200210cfa34a854b082721f902f2bf3207207d31b00773efa99adb822fed13`.
Original source conflicts, analytical rights, biological interpretation and
qualified chronology decisions remain separate acceptance questions.


## Goat locality coverage and source-owned atlas admission

The [locality-support protocol](adna-locality-support/protocol.json) binds a
single-species followthrough for the already qualified goat source. Its v2
exports already retained 78 specimens and 78 separately owned chronology
packets, but their 23 locality hulls still carried specimen-level dating
labels. The maintained `build_species_normalization_bundle("Capra hircus")`
and three native export helpers now supply the verified correction.

Only `dating_basis`, `evidence_class` and `precision_posture` change on each
aggregate, to `locality_sample_coverage`, `locality_sample_coverage_hull` and
`display_coverage_only`. Every specimen, ordered membership, coordinate,
original date text, endpoint, midpoint, uncertainty field, source/provenance
packet and all eight refusals remain exact. This is **69 label changes in
each of JSON, CSV and bundle**, representing the same 23 localities rather
than additional observations. Only those three generated files are installed;
the other 1,678 animal-data files remain byte-identical.

The actual producer passed at
`bba372a6f1745b89d7afae20041f54dfa145491c` in 3.23 s, with 96,960,512 B peak
RSS and 2,194,072 B final products, within 60 s / 1 GiB / 16 MiB. Its guards
bind all 4,584 tracked Python files, HEAD, index, protocol, 1,681 animal-data
inputs, two repository descriptors and 259 actual opened resources. The
reference-stash lookup is absent and separately recorded. All 219 directory
lookup attempts remain in their original authenticated readset.

Two observer errors remain retained. First, it treated Python's missing
optional `python311.zip` import lookup as a successfully opened directory.
Second, it expected Python's `False` spelling where the maintained CSV
formatter requires `false`. The successful same-epoch readback permits only
that exact absent runtime probe and corrects only the one CSV boolean
expectation. It preserves the original products, all other checks and both
failed attempts; no normalization retry or numerical tolerance change occurred.
Both limited runtime adapters and their own hashes are recorded in the result.
Successful observation took 2.63 s, with 38,404,096 B peak RSS and 2,594 B
output, within 60 s / 512 MiB / 8 MiB. Complete products remain in
`artifacts/root/adna-locality-support/capra/`; independent facts are
`artifacts/verification/adna-locality-support-capra/verification.json`
(SHA-256 `6378ea8b8127395abf55d706c9e2b1b2a856d000c6aa0e6881c1eb8e38906e92`).
The data correction is committed at `ab43e5188`; durable observer corrections
and 67 integrated controls pass at `2f4f3b83c`.

The corresponding atlas consumer now resolves complete unique support owners
against exact admitted original sample packets. A persuasive hull alone
cannot admit a locality. Specimen chronology policy remains unchanged; public
locality coverage receives distinct display labels. Python and JavaScript
retain explicit feature refusals and use complete source-owned child intervals
before a merely contextual hull posture. Disjoint dates leave their intervening
gap empty. These changes pass 135 combined controlled checks and static checks;
the actual saved-source taxon/scope regression also passes with all 3,124
consumed core-code and animal-data files stable.

The complete saved-source locality partition, three assembled map surfaces,
independent index readbacks and served temporal checks now pass at
`a18530b54738b71dfef4d69becaf56ae7ecc4827`, as detailed in the
[current population account](#current-source-and-map-population). Their receipts
bind the newly assembled products; earlier map receipts retain their historical
source and build identities. No source date, chronology-node census, biological
identity, field permission or independent scientific decision was newly selected.

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

## Goat comparator identities

The retained PRJEB90141 run export contains **784 technical runs under six
study accessions** and no direct parent accession in its `study_accession`
column. A separately captured [current native project record](https://www.ebi.ac.uk/ena/browser/api/xml/PRJEB90141)
identifies PRJEB90141 / ERP173153 as their umbrella: all six study IDs are its
listed children. Calling those studies unrelated to the project would be
incorrect. All 784 rows reconcile to the six children, with 784 distinct run and
experiment accessions and 721 distinct sample accessions. These are archive
record counts, not a complete biological or genotype population. None of the
five literal benchmark accessions occurs anywhere in that retained export.
The parser's direct-study diagnostic is a literal column comparison, not a
project-hierarchy traversal; it does not establish archive absence.

The [primary paper's Methods and Data Availability](https://pmc.ncbi.nlm.nih.gov/articles/PMC12598287/)
assign PRJEB90141 to the modern VarGoats reference genotypes and ancient imputed
unfiltered genotypes separately to DOI10.17605/osf.io/av4f9. Its starting 1372
reference animals and 1155 after filtering describe different analysis populations.
Neither supplies the deposited project's membership or expected count. The
publication's embargo statement and the current PROJECT metadata's
`ENA-FIRST-PUBLIC=2026-02-17` / `ENA-LAST-UPDATE=2026-02-19` are separate facts;
those attributes do not prove genotype availability or sample release.

The original workbook's Table S3 has 36 named reused ancient analysis units
and 39 distinct accession alternatives, including three composite labels. The
four Table S2 downsampling benchmarks are a subset of those analysis units.
Table S1 instead contains 1155 filtered reference-panel names, and Table S4 has
ten sheep outgroups: seven *Ovis aries* and three *Ovis orientalis*. Repeated
Table S15 analysis blocks do not add another animal. These source populations
must remain separate. Table S3 has no scientific-taxon column; the project-level
Capra hircus annotation cannot be assigned to every record. The retained run
export includes wild Capra taxa and Rupicapra rupicapra.

The full article was received as a separate current response on 27 October 2026
(290306B, SHA-256 `856b785d01d465c10272d6ece56f7b582d270e5b55733d17a3a37d4a47095cf0`),
and the native PROJECT XML as 3530 B
(SHA-256 `88f11ea6fb90dbcc3927452ea02894269941c675355af0027c52c05a391e0e52`).
An independent literal XML/TSV reconciliation agrees in 0.09 s with 23,592,960 B peak
RSS and unchanged bytes. Current child-set agreement does not authenticate
historical request routing, pagination or the undated retained run capture.
No native member or genotype dataset was downloaded, and no genotype analysis
was rerun. The expected PRJEB90141 population remains unknown.

The original accession cells are `SAMEA4453841; SAMEA4453842` for Direkli1-2,
`SAMEA4588077` for Blagotin3, `SAMEA4591761` for Acem2 and `SAMEA4591758` for
Semnan3. The first cell has two alternatives, which cannot be replaced by a
single verified individual. The four stable source-row keys and candidate
accession traces remain inspectable; the identities are now ambiguous
supplementary sample labels. Their source dates, coordinates, locality text and
unreported taxon fields are preserved. The configured species is not proof of
the source taxon, and the Direkli ancestry description remains Turkish Bezoar.
An expected project sample count is still unknown.

The source correction was committed at `6fdc2e972`. The actual master comparison
returned exit zero in 0.91 seconds with 81,084,416-byte peak RSS. An independent
literal TSV/original workbook read confirms all four rows, five accession
alternatives and six-study capture distribution. Exactly six identity/lineage
fields per row change, with final identities four to zero and ambiguity rows
zero to four. The first normalization comparison made an incorrect four-refusal
assumption and compared saved JSON lists directly with in-memory tuples; its
unsuccessful output is retained. The corrected independent diagnosis compares
canonical JSON: all **78** common normalized samples are exactly unchanged;
four samples and four dependent localities are refused. Twenty-three retained
localities additionally expose the already implemented sample-owned chronology
support alongside their coverage hull. Independent candidate review confirms
all 78 components match original individual chronology/provenance, with every
old locality field and order unchanged. No chronology is selected from a hull.

### Current source and map population

The qualified 48-file source/normalization candidate is installed. Its actual
qualification at `83bb2e81e` passed in 2.208774291 s with 160,055,296 B peak
RSS; all 1,963 consumed inputs remained stable. All **1,475 source rows** remain,
including the four ambiguous goat source keys and five accession alternatives.
Their dates, coordinates, locality text and source-taxon fields remain unchanged.
At that qualification epoch, the 23 common Capra localities retain every old field and its order; three
existing sample-chronology support additions are retained, without selecting a date
from the coverage hull.

The current source chronology partition is **319 admitted + 1,156 refused =
1,475**. The exclusive refusals are **11 identity**, **789 chronology** and
**356 coordinate** decisions. World displays 319 temporal nodes; Europe-plus
and Nordic each retain **13**. Nordic's temporal-node country counts are Denmark
seven, Finland two and Sweden four. These are distinct from the point-locality
population in the [entity account](animal-entity-capability/README.md): **1,464
normalized IDs = 324 mapped IDs in 163 features + 1,140 exclusions**. Its Nordic subset remains twelve
mapped IDs in eight features: Denmark five, Finland two and Sweden five.
Neither partition establishes biological independence or scientific admission.

The [complete saved-source observer](../../artifacts/verification/adna-locality-atlas-consumer/verification.json)
verifies all normalized owners and all 37 native products against their source
packets. Two existing horse localities, Hyena's Lair and Yana in PRJEB44430,
now contribute six previously excluded source owners. No feature or mapped
owner was removed. This is source-owned locality visibility, not six new
specimens, dates or biological admissions. Hyena's Lair remains contextual with
no numeric occurrence interval; Yana exposes only its individually dated child's
30,517 BP point. Other undated children remain undated.

World's 163 locality points contain **225 child-support intervals across 126
temporally admitted points**, alongside **37 contextual points**. The independent
source comparison preserves **60 gaps** between disjoint supports: the locality
display hull cannot fill them. These interval and feature counts are not counts
of independent ecological events. Europe-plus and Nordic each retain eight
locality points, twelve source owners and eleven child-support intervals.
The source consumer took 4.61 s with 159,088,640 B peak RSS; its independent
observer checked 4,729 tracked package files, 1,681 animal-data files, 101 opened
resources and 194 directory discoveries without invoking a normalizer, model or
source chronology census.

The current three-scope map producer closed at the same source epoch in
326.10 s internally (327.24 s process wall time), with 4,992,991,232 B peak RSS
and 126,381,319 B of generated products, within 600 s / 8 GiB / 192 MiB. The
[independent preservation result](../../artifacts/verification/adna-locality-map-preservation/verification.json)
verifies exact unrelated decoded points, polygons, details, signals, edges and
sequences, and exact source-owned animal layers. All **319 World source
chronology nodes** and the thirteen in each regional scope remain exact; their
sidecars retain their original snapshot identity byte for byte. This reuses
qualified source context rather than claiming a new current chronology census.
The preservation check took 34.17 s with 715,866,112 B peak RSS.

Actual packaged-JavaScript index readbacks pass for
[World](../../artifacts/verification/adna-locality-map-index/world.json),
[Europe-plus](../../artifacts/verification/adna-locality-map-index/europe-plus.json)
and [Nordic](../../artifacts/verification/adna-locality-map-index/nordic.json).
World and Europe-plus use freshly reconstructed independent UTF-16 postings
references; Nordic uses complete document equality to its authenticated historical reference
before rechecking the current packaged factory. Nordic retains all 263,708
documents, 11,386 posting keys and 35,103,623 memberships. The four independent
preservation/index processes closed in 65.52 s combined, within their shared
180 s ceiling. The per-scope wire, chunk, request and document budgets remain
unchanged. These checks establish complete index semantics, without measuring
query latency.

The [served Chromium observation](../../artifacts/verification/adna-locality-served-temporal/observation.json)
passes **22 cases: eighteen source-backed cases and four labelled synthetic
controls**. It executes the freshly served maintained temporal functions,
checks dated-child visibility and disjoint gaps, and leaves contextual horse
members without numeric dates. A source-backed SEAD display envelope with a
zero endpoint spans [0, 10,000] BP; it is not evidence of an exact source date
at zero. The exact [0, 0] BP point is a separate synthetic control, alongside
explicit global-refusal, duplicate-owner and negative-endpoint controls.
The browser check took 2.39 s internally (2.72 s process wall time), recorded
no runtime errors and restored the original UI time window. It qualifies those
served cases, not a general browser, filtering-latency, field or event claim.

The installed source/map products also pass the thirteen-input entity replay:
1,464 = 324 + 1,140, with the twelve-ID Nordic subset unchanged. Existing source
requests, source-country authority and biological/chronology reviews remain
pending. The following saved-population and map receipts describe earlier
qualified epochs; they are retained rather than substituted for these actuals.

The separate saved-population global chronology review ran at
`6e68f1a9d6d6b51ddcb487abdf3edd7d80b76623`, with the governed chronology and
provenance populations supplied together. All 1,475 owners reconcile; only the
four known rows' six identity/provenance fields change. The other **1,471 rows**,
every date and classification totals are unchanged. Eight focused
source-access/owner controls, configured Ruff and strict types pass. The actual
consumer exited zero in 0.67 s with 116,424,704 B peak RSS, within
60 s / 512 MiB / 8 MiB. Its 2,144,216-byte JSON is now
[installed](../../docs/report/animal_sample_chronology_review.json), SHA-256
`4cb3827cae92baddb2a37913ba4932272b313f2b3d3c19d76b793fbd0715b4ef`.
This saved-population comparison did not invoke an original-project builder;
the subsequent source/map execution below is a separate qualification.

The earlier complete World, Europe-plus and Nordic map producer passed at
`04f1c48579ad39775ac116cee6df1f7a858e74de` in **266.41935075 s**, with
**4,658,364,416 B** peak RSS. All **2,617 inputs**, HEAD and index remained
stable. The candidate under
`artifacts/root/goat-source-qualification/governed-model-map-candidate/`
produced **128,356,107 bytes**, within its declared 600 s / 8 GiB / 192 MiB
execution bounds. All three scopes passed their source, native chronology,
temporal projection, layer, CSS, glyph and playback checks. Nordic has **239
static assets / 75,446,344 wire bytes**, including **two index parts /
6,168,753 bytes**. The existing bootstrap, chunk, document, total-wire and
request limits remain unchanged.

The compact search transport retains all documents and deterministically
restores the original postings. An independent
[actual packaged-JavaScript observation](../../artifacts/verification/index-transport/full-index-observation.json)
passed with **30.51 s process wall time** and **1,320,927,232 B** peak RSS, within the separately
declared 120 s / 2 GiB bound. All **275,094 entries** agree with the retained
original: **263,708 documents**, **11,386 posting keys**, **35,103,623
memberships** and **21,949,771 UTF-16 units**. Their complete framed semantic
SHA-256 is
`d45e9e74031c8e34d17f80ddb992a5366345d5a289006f5d1f0eed4b57380f17`.
This establishes full search-map correspondence and that observer's resource
result. It does not establish actual query execution, full-browser behavior or
the 50 ms filtering claim.

### Retained execution failures

The unsuccessful comparisons and map attempts remain under
`artifacts/root/goat-source-qualification/` and
`artifacts/adna/goat-imputation-source-qualification/normalization-diagnosis/`.
The initial normalization assumptions and tuple/list comparison failure are
separate from the corrected native comparisons. An earlier Nordic map attempt
exposed the fixed 4 MiB outer index-container limit. Partitioning that container
preserved the logical content, but a subsequent candidate still exceeded the
128 MiB total-wire limit: 186,450,628 bytes, including 117,173,037 index bytes
across 31 parts. No partial map from those attempts was installed.

The documents-only candidate then passed static-asset validation but stopped
at modeled-context validation after **179.36 s / 5,590,646,784 B** peak RSS.
That boundary compared dictionary insertion order after canonical JSON and
failed to admit the producer's explicitly projected `no_pollen_data` all-null
metric pairs. The maintained validator was corrected without changing source
values, source metric-key order or the null-data decision. The complete
qualified producer above supplies the later successful map result; the failed
attempt remains a failure.

Seven current source, published-chronology and sample-evidence regressions pass
in 38.94 s, with configured lint, formatting and strict types for the three
affected test files. All 74 scientific accounts, 285 reader routes and 36
external review questions validate; zero qualified review decisions are received.
The full output-ownership check remains blocked by its pre-existing unrelated
ABBO declaration gap: 2,250 tracked report paths versus 2,249 declared paths.
The changed publisher partition's 700 paths pass exact membership, existence,
ordering, uniqueness and inventory-digest checks. Three generated runtime assets
retain their producer's trailing whitespace because their qualified bytes,
manifest digests and integrity attributes are preserved; all other staged paths
pass the whitespace check. The counts in the following horse account describe
its earlier source epoch.

## Historical horse chronology display

The source correction retains all **260** rows from the [245-row horse time
series](../../data/adna/governance/source_library/projects/PRJEB31613/sample_master.json)
and [15-row comparative panel](../../data/adna/governance/source_library/projects/PRJEB19970/sample_master.json).
It removes **250** previously inferred BP intervals: 237 and 13 respectively.
Native identifiers, source tokens and unrelated sample fields are preserved.
The separate Nature 2021 source has an explicit `AgeEstimate (BP)` field; its
248 source rows and chronology records remain unchanged.

At that historical source epoch, across **1,475** rows the horse-corrected
chronology display admitted **323** nodes and refused **1,152** rows. Its
exclusive refusal waterfall contained
**7** unresolved sample identities, **789** non-comparable chronologies and
**356** unmappable coordinates. The earlier display admitted 557 nodes.
Removing unsupported intervals removes **234** world features; the other
**16** affected rows were already refused for coordinates and now fail at the
earlier chronology check. The two `Palm143` identity refusals are unchanged.

The [world](../../docs/report/world/world_animal_sample_chronology_context.json)
display then included all 323 admitted nodes. [Europe-plus](../../docs/report/regions/europe-plus/europe-plus_animal_sample_chronology_context.json)
and [Nordic](../../docs/report/regions/nordic/nordic_animal_sample_chronology_context.json)
each then included **13**, after removing one unsupported horse chronology feature.
These regional counts are projections of the same global source corpus; the
1,152 refusal rows describe that historical corpus rather than a new regional
denominator. The linked governed files now carry the current goat correction
above; the 323/1,152 figures are retained historical counts.

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

**Supported claim.** All 260 horse source identities and native elapsed-age tokens are preserved; 250 unsupported BP intervals are refused. The PRJEB31613 provenance consumer additionally preserves 1,960 labeled source-date cells for 245 owners and separately accounts for 54 signed-calendar alternatives against the source-defined 2017 reference: 18 equal numeric D coordinates, 35 different and one range left uncomputed. All 191 blank alternatives and every selected chronology remain unchanged. Generic direct radiocarbon evidence and precision remain refused; Palm143 identity refusal is retained. Separate Galician curation exposes eleven sample-owned supplement rows as 110 literal typed cells, with radiocarbon, calibrated-BP, calendar and locality fields kept distinct. Palm143 source curation distinguishes one author Table S1 sample/find row from capture and shotgun technical representations across two BioSamples, without selecting physical specimen identity. The Baltic sheep source explicitly binds five project-owned individuals; administrative expected/recovered accounting is five/five. Four PRJEB90141 comparator keys/five candidate accessions retain ambiguous identity, with literal alternatives and every source date/coordinate preserved; modern VarGoats reference genotypes and ancient imputed data are distinct source roles. Source-specific Obishir AA-114607 stratigraphic warning now reaches one owner conflict/review fields and exact temporal provenance. Sheep export preserves200samples/3refusals/9localities with200individual chronology supports; locality hulls are display-only and never replace sample dates. Capra exports now label 23 coverage hulls as display-only while preserving all 78 specimens, 78 owned chronology packets and eight refusals. Atlas locality admission and occurrence filtering now use exact sample-owned support; current actual saved-layer/map/runtime qualification now passes in its stated scope. PRJEB41594 source inspection distinguishes six selected/extracted specimens from five advanced deep-shotgun samples and five retained archive aliases; expected/unresolved biological counts remain null, with explicit source_population_unresolved provenance. PRJEB75467 expected population is50source-declared new samples, separate from44captured BioSamples/45masterrows; administrative unresolved count6 retains Fre1 and alias ambiguities. PRJEB31621 distinguishes66ancient sourceIDs/77archiveowners/78unionrows and keeps project expected populationnull.

**Unsupported claim.** A universal 67-year shift, calibrated BP, or per-row direct radiocarbon support from the imported mixed elapsed-age field; distinct physical identity for both Palm143 BioSamples; ecological events. The four comparator keys do not authenticate distinct selected specimens, and current project hierarchy does not authenticate historical export routing or genotype availability.

**Actual verification performed.** The alternative consumer ran at d9a4ea9a3653cd6c07a0f924e1259b5ccac8eede, session 80537 exit zero: all 54 source midpoint/offset equations hold, all 245 owners and 191 blank refusals reconcile, and all 1,475 previous packets and selected fields remain unchanged. The independent DOM/rational saved-result and original literal observers passed three tests at 547d24718cca48d8deaa2e00b0441d3b2418139f, session 75988, confirming all alternative/source counts and unchanged packets. The producer’s initial wrapper-comparison failure and same-source correction are retained above. The horse source-field consumer and independent raw-XML test ran at a1f04506dd1a26ea63cda0f2c3526814629fc995, both exit zero: all 245 source owners/1,960 date cells agree, with 1,475 old provenance packets unchanged and no new field on the other 1,230. No map or selected-age writer was rerun for this source-field result. Earlier actual owned source and dependent-data consumers, three qualified map surfaces and five paired final/public/governance owners returned; baseline drift was zero and immutable source/country/map inputs were preserved. World/Europe actual returned predecessor stages were retained with the CSS-only renderer; Nordic was freshly published. The index did not rerun. The Galician optional consumer ran at 85de3133f, exit 0 in 2.30 s, producing a 19905-byte context table. An independent DOM source check confirms all 110 cells, original header/unit/type/style/value/blank/formula states and exact eleven crosswalk rows.Fifty controlled tests plus the native default-writer exact-byte test pass, with configured lint/types. Original default report/species CSV remain unchanged. Original nested DOCX was streamed in place without materializing its 170976839 bytes; only document.xml and retained primary HTML were read. Independent literal-layout checking confirms the ten non-sequence header/target cells and four author-label occurrences, including a physically present empty WGSS cell. Original ZIP identity and both identity refusals remain unchanged. Actual reading .42 s/RSS75464704 B; separate layout check .29 s/RSS81756160 B; the actual report render and 24 reader controls pass. The Baltic one-project consumer at 92b5042fc3dd327c7ea42445044610a9bb905b9c passed: exactly five master header fields differ, all five rows and 18 guarded inputs are unchanged, and five material conflicts remain. No global completeness or intake view was regenerated. The later 48-file goat source candidate at 83bb2e81e passed exact support/input checks in 2.209 s; the matched saved global review at 6e68f1a9d changed only four identity/provenance rows. The full three-scope producer at 04f1c4857 passed in 266.419 s/RSS4658364416 B, with all2617 guarded inputs stable and original budgets unchanged. The independent actual Nordic JavaScript index observer passed in30.51 s/RSS1320927232 B: all275094 logical entries and35103623 postings memberships match the independently authenticated original. Seven current source/map/evidence regressions pass in38.94 s. Earlier failed attempts are retained; no full browser, query-latency, new dating or biological review claim. At e9aff4a34 actual chronology producer11.02s/RSS262864896B/37254885generatedB and independent1.69s/RSS151863296B verify260products/1475owners, exact1Obishir note delta and explicit unrelatedhorse additions left uninstalled; source/code/index guards pass. The first exact Markdown-header observer refusal is retained; only two ordinary header lines admitted on readback, products unchanged. Supplied-population public reader changes only two notes on this owner and preserves aggregates/authored body; original whole-page/footer assertion failure retained. At7053f6edc actual sheep producer3.10s/RSS84983808B and independent1.67s/RSS30556160B verify all200sample identities/fields (one caution),3refusals,9locality identities/coords/bounds,200owned support joins and4export pins;4542Python/1677source guards stable. Twelve source-caution and seven hull controls plus configured lint/format/types pass. No calibration/model/map/new source. At bba372a6f1745b89d7afae20041f54dfa145491c the actual single-species builder and native exporters pass in 3.23 s, 96,960,512 B RSS, 2,194,072 B final output. Same-epoch independent readback passes in 2.63 s, 38,404,096 B RSS, 2,594 B output: 78 specimens, 23 localities, 78 supports and eight refusals exact, with only 69 aggregate-label changes per format. All 4,584 Python files, 1,681 animal inputs, 259 actual opened resources, two descriptors and source epoch remain stable. Two observer contract errors are retained: an absent optional Python import ZIP probe and expected uppercase CSV boolean. Explicit recorded runtime adapters correct only those metadata expectations without producer retry, product edit or numerical change. Data ab43e5188 and durable observer fix 2f4f3b83c preserve all other source fields; 67 observer controls and 135 combined locality/Python/JavaScript controls pass, with configured static checks. The saved-source core taxon/scope regression passes with 3,124 consumed core/data files stable. At a18530b54738b71dfef4d69becaf56ae7ecc4827 the actual saved-animal producer and independent observer first pass preserve all1464 owners:324 mapped in163 features and1140 reasoned exclusions; all4729 tracked package files/1681 animal inputs/101 opened resources/194 discoveries remain stable. Two newly visible horse localities retain six original owners (Hyena's Lair contextual, Yana only its supported child date); no dates are invented. World126 timed-admitted/37 contextual features retain225 child intervals and60 disjoint gaps. The necessary three-scope map producer first passes327.244s/RSS4992991232B/126381319 generatedB within600s/8GiB/192MiB;7181 inputs/2325 actual reads and source epoch are stable. Independent decoded scientific preservation and all three current packaged JavaScript factories first pass in65.517s aggregate within180s, with all unrelated records and319 retained source nodes exact. Nordic275094 search entries/35103623 posting memberships match a fresh full-document equality bridge to authenticated prior proof, followed by actual new-wire JavaScript restoration. Current served World Chromium closure first passes22 cases in2.718s/full-process-treeRSS1236041728B:18 source-backed cases/four explicit synthetic controls,25 served files,zero runtime errors and restored UI state. Site5070 retains its0–10000BP display envelope; the0BP point is explicitly synthetic. No query-latency, fullUI, new source census, field or biological admission claim. At8fa209201bb67906699a9ee02112ee92f0059ec7 the maintained one-project master consumer/exact comparison passes2.07processs/RSS78331904B within60s/512MiB/8MiB; all6126source/inputfiles and HEAD/index remain stable. Only three expected-population metadata headers change; all5rows remain exact,4Ovis+1Capra, expected/unresolved countsnull. Two existing source-native taxonomy controls and configured lint/format/types pass. Independent original ReportingSummarypp2-3/article/AppendixF/ENA review agrees. Initial wrapper comparison failed because native as_dict omits materializer schema_version; corrected existing envelope preserves originalfailure and changes no source/data/criterion. No global materializer/census/model/map/acquisition ran. At8fe41f69d700a23eb30bdc6bd296d25fa399cdcb the two-project consumers/exact row comparison first pass2.15processs/RSS89784320B within60s512MiB8MiB, all6126source/inputfiles+HEAD/indexstable. Only3PRJEB31621/5PRJEB75467 metadataheaders differ; all123rows exact. Two existing taxonomy/recovery controls plus6projectsubtests and scoped staticchecks pass. Independent primary PDF/workbook/XML/ENA review confirms50new sourceIDs,66ancient sourceIDs and separate44/77captured owners. No genotype/model/globalmaterializer/census/map/sourceacquisition ran.

**Remaining input or review.** The Cell 2019 native selected Age (years ago) field still has no established field-specific epoch and scale mapping; the separate T–X alternative arithmetic is now source-bound to 2017 without adopting a civil year-zero convention; a mixed project dating basis cannot classify every row as direct radiocarbon. Two Palm143 BioSamples also retain unresolved physical specimen identity. Four goat comparator keys/five candidate accessions also need source-backed specimen ownership and historical project-to-export reconciliation. PRJEB41594 requires a source-owned six-to-five analysis-stage crosswalk and closed project submission roster; five archive aliases do not establish its expected biological denominator. PRJEB31621 still needs Men1/MV013 and modern ERS/SAMEA/project-scope bindings; PRJEB75467 still needs six unmatched AnalysisID and Borly4a/Borlya source identity resolutions, preserving sample-specific use restrictions. Resolver: Horse source chronology reviewer and SRP073444 specimen/source owner; goat specimen and project/export source owner Reopen when: Source-backed field epoch and scale or independently dated per-row evidence permits horse chronology; citable accession-to-physical-specimen evidence resolves Palm143. Source-backed goat comparator-to-accession identity and historical export population reconcile.

**Cause category.** data|assumption

**Consequence.** Source chronology nodes, locality features and mapped samples have distinct admission contracts. Elapsed-age text cannot become BP or direct radiocarbon support, and accession labels cannot establish independent specimens.

**Precise next acceptance route.** Resolve the selected D field meaning, per-row dating evidence and source conflicts before re-admitting horse chronology; preserve the now-accounted alternative coordinates as distinct source context. Resolve Palm143 physical specimen identity from citable source evidence before revising its source-sample publication decision. Use the source treatment distinction now; obtain the specific accession-to-extraction-to-physical-bone crosswalk before changing Palm143 identity or dependency grouping, without requesting the already retained supplement again. Obtain the Obishir specimen-to-stage crosswalk and explicit project submission roster before replacing null expected population; retain all original identities/dates/taxa and archive versus study denominators. Reconcile Men1/MV013 and modern ERS/SAMEA/project membership for31621, and the six unmatched new-sample IDs plus Borly4a/Borlya files for75467 before whole-project biological completeness or independent-individual claims.

**Negative or refused result.** 250 previously inferred BP intervals are refused; all 260 selected horse dating-evidence and precision classifications remain unresolved. Among the 245 linked source-field rows, 191 have blank R–X cells and eight have literal `-` in D; all 54 populated alternatives are arithmetically consistent, but 35 numeric D values differ from their alternative midpoints and one range is not compared. No selected chronology is established by this accounting. The global refusal waterfall has 11 identity, 789 chronology and 356 coordinate refusals. Both Palm143 accessions remain identity-refused. Galician sample SAMN18106837 keeps modern-carbon text, a blank calibrated-BP cell and last-60-years calendar text; its label establishes neither 60 BP nor Cobas locality. All eleven retain unresolved site/date and refused atlas-point posture. Table S1 WGSS is blank while Table S3 separately includes a shotgun row. The two accession titles distinguish capture/shotgun treatment, and extraction independence does not establish specimen independence. Exact accession-to-extraction-to-bone binding remains absent; neither collapse nor independent biological counting is adopted. Four goat comparator identities are ambiguous before normalization; the current global chronology has319 admitted/1156 refused records. All six retained technical studies are current project children, so they are not labeled foreign contamination; five comparator candidate accessions are absent from the retained export, without asserting live absence. OB20-04 warning adds one conflict/attention owner; existing publication owner predicate blocks it, no whole gate rerun. Its null coordinates retain map exclusion. Two Obishir aliases remain undated. Sheep has26/200samples without numeric endpoint pairs and3original recovery refusals; coverage hulls cannot fill chronology gaps or establish dated observations. Locality hulls cannot admit unsupported specimen dates or fill gaps. The current point partition, three-scope maps, complete index restoration and bounded served-runtime checks now pass;37 World locality features remain contextual, and six newly mapped owners gain no dates from their coverage hulls. No field, fullUI or latency qualification follows. PRJEB41594 expected/unresolved population staysnull:6selected/extracted,5advanceddeep-sequencing and5ENAaliases are different stage denominators. Capra SAMEA8022722 remains project_species_mismatch; no fifth-sheep or independent-individual claim. PRJEB31621 expected/unresolved remainsnull and provisionalMen1 isnotautomaticallyMV013. PRJEB75467 administrative6=50expectedminus44finalarchiveidentityrows isnotauthenticatedsixmissingindividuals; provisionalFre1 and Borly4a/Borlya ambiguity persist. Publishedmixedtaxonomy and eightASIAPASTnoncommercial-use limits remain; no taxon/biological/rights admission.

**Matched denominator.** 1,475 source rows = 319 temporal nodes + 1,156 refusals; 13 temporal nodes each in Europe-plus/Nordic. Separate normalized foundation: 1,464 rows; current locality atlas:163 features/324 mapped samples; 12 Nordic mapped IDs. Separate Galician context:11 BioSamples versus 18 paper specimens;110 exact cells: 109 shared strings, one present blank, zero formulas. Separate Palm143 context: two BioSamples/experiment-run pairs, one Table S1 sample/find row, two Table S3 treatment rows and one Table S5 repeat; four author-label occurrences are not four specimens. Separate PRJEB59481 source population: five expected, five recovered, zero unresolved count; five unchanged material conflicts. Separate source-caution population1475owners, one changed review owner/1474preserved; attention928to929/conflict0to1. Separate sheep200normalized samples+3refusals,9localities/200exact membership supports,174numeric pairs/26without. These are not additional source specimens or independent time observations. Capra followthrough: 78 specimens, 23 localities, 78 supports and eight refusals; three aggregate labels on each of 23 localities, reflected in three formats without increasing the observation count. All other 1,678 animal-data files remain byte-identical. Separate Obishir population inspection:6selected specimens/6extracted teeth,5advanced samples,5retained runs/5experiments/5BioSamplealiases=4Ovis+1Capra; these are dependent stage counts, not a closed biological census. Separatebovine sourcepopulations:75467 published50new samples(41Bosprimigenius/8Bostaurus/1Bosadmixed),664runs/44BioSamples,45masterrows=44final+1provisionalFre1,6administrativeunresolved.31621 source66ancientIDs,9newmodern versus14reusedmoderns;364runs/77BioSamples,78masterunion=65ancientjoins+12archiveonly+1provisionalMen1. These are not interchangeable specimen/analysis/archive units.

Retained evidence: [data/adna/governance/source_library/projects/PRJEB31613/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB31613/sample_master.json), [data/adna/governance/source_library/projects/PRJEB19970/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB19970/sample_master.json), [data/adna/governance/source_library/projects/SRP073444/sample_master.json](../../data/adna/governance/source_library/projects/SRP073444/sample_master.json), [docs/report/animal_sample_chronology_review.json](../../docs/report/animal_sample_chronology_review.json), [reports/science/source-cohorts/galician-sample-context.csv](source-cohorts/galician-sample-context.csv), [artifacts/animal-source-chronology/native-source-fields/summary.json](../../artifacts/animal-source-chronology/native-source-fields/summary.json), [artifacts/animal-source-chronology/source-alternatives/summary.json](../../artifacts/animal-source-chronology/source-alternatives/summary.json), [data/adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html.gz](../../data/adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html.gz), [data/adna/governance/source_library/projects/PRJEB90141/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB90141/sample_master.json), [data/adna/governance/source_library/projects/PRJEB90141/sample_chronology_provenance.json](../../data/adna/governance/source_library/projects/PRJEB90141/sample_chronology_provenance.json), [data/adna/governance/source_library/projects/PRJEB41594/sample_chronology.json](../../data/adna/governance/source_library/projects/PRJEB41594/sample_chronology.json), [data/adna/species/ovis_aries/normalized/sample_records.json](../../data/adna/species/ovis_aries/normalized/sample_records.json), [data/adna/species/ovis_aries/normalized/locality_summaries.json](../../data/adna/species/ovis_aries/normalized/locality_summaries.json), [reports/science/adna-locality-support/protocol.json](adna-locality-support/protocol.json), [reports/science/adna-locality-support/atlas-consumer-protocol.json](adna-locality-support/atlas-consumer-protocol.json), [reports/science/adna-locality-support/map-followthrough-protocol.json](adna-locality-support/map-followthrough-protocol.json), [data/adna/final/atlas/animal_atlas_point_candidates.json](../../data/adna/final/atlas/animal_atlas_point_candidates.json), [data/adna/governance/source_library/projects/PRJEB41594/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB41594/sample_master.json), [data/adna/governance/source_library/projects/PRJEB31621/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB31621/sample_master.json), [data/adna/governance/source_library/projects/PRJEB75467/sample_master.json](../../data/adna/governance/source_library/projects/PRJEB75467/sample_master.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
