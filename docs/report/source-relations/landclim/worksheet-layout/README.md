# Source worksheet layouts and cached values

The selected EKE, GIL, KRO_NY and RASH originals contain **eight worksheets**, all observed as visible. A source-bound sidecar now preserves each sheet's native visibility code, order, name, dimensions, merged ranges, character-decoding metadata and cached error codes. Hidden and very-hidden sheets are preserved by the contract; the selected originals contain neither. This is a four-workbook observation, not a census of all 79 workbooks.

The [account](report.json) retains **27,325 exact cached cell/type comparisons** and unchanged historical sheet-record hashes. The separate raw record comparison checks sixteen BOUNDSHEET name and visibility fields. KRO_NY uses the legacy BOF `0x0500` and codepage 1252; the other three originals use BOF `0x0600` and codepage 1200. Legacy ASCII sheet names and BIFF8 compressed Unicode names have different source layouts. The oracle reads those fields independently from the worksheet API while sharing xlrd's CompDoc container decoder. It does not recover every physical BIFF record or formula token.

All eight selected sheets have no decoded merged ranges or cached error cells. Four auxiliary sheets are empty and remain in the sidecar. These observations do not imply that other workbooks lack hidden sheets, merged cells, errors or external links. Source spelling is retained: ordinary roster selection refuses `KRO_ny.xls` when the captured member is `KRO_NY.xls`, including on a case-insensitive filesystem.

## Separate row and formula evidence

The earlier actual EKE consumer remains its original execution: all 1,376 cached values and types matched, and 42 mechanical rows partitioned into 25 positive-feature and seventeen zero-feature rows. Subtracting those seventeen from the retained 5,170 mechanical rows gives the metadata total of 5,153 under the declared row partition. Twenty-four positive EKE rows contain noninteger features. We did not repeat the other 78 workbooks' feature census or authenticate grain counts, interpolation, observed sample status or ecological absence.

Native XLS values in the selected sidecar are cached decoder outputs; that sidecar does not identify formula provenance. A separate physical-record account now locates formula records across all 79 retained workbooks, as described below. A later bounded account qualifies affine expression syntax and shared-definition bindings for these source age fields. Their source values, reference units, calibration and derived-age interpretation remain unqualified; no formula or source age is evaluated or converted. Formula cells and external-link parts in the separate OOXML metadata path remain subject to its maintained refusal contract. Those cell and formula runs did not reopen the original archive or perform a malware scan or source-rights decision. The separate bounded member comparison below now revisits the exact retained archive without filesystem extraction.

## Actual checks and limits

The [custody account](source-account.json) retains the complete execution chain. The first oracle attempt failed because it treated a legacy name as BIFF8. The corrected scientific stage returned zero; its larger check job later failed only on a redundant cast in a positive test. Removing that runtime-no-op test cast left the producer unchanged. The final nine affected tests, configured Ruff and formatting, and strict typing of both source and tests passed. The earlier corrected stage also passed 55 source/security/layout tests and two mechanical header tests. These receipts preserve actual failures and stage exits rather than labelling the failed larger job successful.

The native stage used a prepared source overlay identified by its physical producer hash; that module was not tracked in the recorded baseline candidate. The native sidecar, individual cached records and controlled fixtures remain local. This public aggregate establishes source preservation under an exact parser contract. Taxonomy, feature units, chronology, original historical membership, PPE, analytical-use rights and scientific admission remain unresolved.

## Reproduce the private sidecar

With the pinned xlrd 2.0.2 optional `rootsi-review` parser available, set `ROOTSI_WORKBOOK_STORE` to the exact private workbook store and `ROOTSI_TYPED_REVIEW` to the retained typed-cell review directory. Choose an absent artifact destination. The maintained decoder and source binder are used directly:

```python
import os
from pathlib import Path

from bijux_pollenomics.collection.sources.rootsi.cells.decoding import parser
from bijux_pollenomics.collection.sources.rootsi.cells.inputs import bind_capture, output_path
from bijux_pollenomics.collection.sources.rootsi.cells.layout import worksheet_layout_records
from bijux_pollenomics.collection.sources.rootsi.cells.models import encoded

store = Path(os.environ["ROOTSI_WORKBOOK_STORE"])
review = Path(os.environ["ROOTSI_TYPED_REVIEW"])
names = ("EKE.xls", "GIL.xls", "KRO_NY.xls", "RASH.xls")
capture = bind_capture(
    inventory_path=review / "capture-inventory.json",
    expected_inventory_sha256="3353156471c2d04f2dce4138d29ad1a4891896d223c2c37dd5c531ba51c17b5a",
    workbook_files={f"rootsi/{name}": store / "rootsi" / name for name in names},
    scope="selected_workbooks",
)
destination = output_path(Path("artifacts/science/rootsi-native-layout"), capture)
destination.mkdir(parents=True)
decoder = parser()
with (destination / "worksheet-layout.jsonl").open("wb") as stream:
    for item in capture.workbooks:
        for record in worksheet_layout_records(item, capture.archive_sha256, decoder):
            stream.write(encoded(record))
```

The resulting private sidecar must match the `worksheet-layout.jsonl` hash in the custody account. The command makes no scientific or source-use decision.

## Physical records across the retained workbook corpus

The separate [physical BIFF account](physical-biff.json) examines all **79 retained original workbook byte streams** and finds 107 BOUNDSHEET tabs, all worksheet type and visible. Those names and source order match the earlier 107-worksheet capture, including its 28 empty sheets. It reads 54,419 physical records without decoding or recounting any cached cell rectangle. The earlier 547,330 cached positions, merged-range records and error-type counts remain retained evidence, not a new cell census.

Sixty-two workbook globals use the BIFF5/7 `0x0500` header and seventeen use BIFF8 `0x0600`. RANV and TRE have BIFF5/7 globals with BIFF8 worksheet headers. The parser preserves each native header separately: BOUNDSHEET names use the global name grammar and physical formula-address bounds use the local sheet grammar. The first full-corpus attempt refused this mixed-header condition after 48 workbooks; its receipt and partial products remain separate from the successful successor. Preserving the source anomaly does not certify that historical cached values were interpreted correctly.

The physical pass finds **63 FORMULA records**: 36 in HAGG and 27 in KYLL, all in the second native column. The retained first-row header in both is `Sample age (cal AD/BC)`. These cached source age fields therefore have formula provenance. The physical-record run executes no formulas and silently converts no source ages. The later affine-syntax follow-up below does not qualify original age-model inputs, source reference units, calibration or chronology interpretation. It makes no grain-count formula claim. Detailed record offsets, row/column associations and payload hashes remain private.

The inspected Workbook/Book streams contain no observed EXTERNNAME `0x0023`, EXTERNSHEET `0x0017` or SUPBOOK `0x01AE` records. This is a bounded record-presence statement; other compound-document streams, macro content, reference targets and security remain outside its scope. The parser refuses unsupported container extents, ambiguous stream aliases, truncated records, invalid flags and offsets, encrypted FILEPASS records, unsupported local headers and contradictory substream types.

A second source-pinned implementation uses xlrd's on-demand workbook-global parser to compare names, visibility, tab totals, BOF class and CODEPAGE. No cached worksheet is loaded. The two methods share xlrd's CompDoc container decoder, source bytes and interpreter. The actual successor returned zero with **38 focused controls**, configured Ruff and formatting, and strict typing of source and tests; all 1,530 source pins, 85 private-source pins and the runtime pin remained unchanged. The [physical source and execution account](physical-biff-source.json) preserves the failed predecessor, native outputs, independent global-field checks and exact maintained producer identities.

The maintained boundary is `bijux_pollenomics.collection.sources.rootsi.cells.biff.physical_biff_structure`. It accepts the pinned source bytes and pinned `xlrd.compdoc.CompDoc` decoder, returning a private record sidecar. For one already bound `WorkbookInput`, use `read_bytes(item.path, item.sha256, item.byte_count)` and pass those bytes to `physical_biff_structure`; this performs no cell-grid decoding. Keep that result in an owned private artifact destination. Original archive intake and scientific interpretation remain separate: this account assigns no taxonomy, pollen-count denominator, PPE, chronology probability, historical study membership or analytical-use rights.

## Source age formula operators

The initial [retained-token inspection](age-formula-operators.json) slices the 63 previously located FORMULA records from two already owned artifact byte payloads. It inspects 1,131 formula-token bytes, reads no canonical original workbook and loads no cached cell grid. All **63 strict 1950-template qualifications remain refused**: 36 formulas refer to shared definitions that were not supplied to this inspection, while 27 contain multiplication and addition outside its qualified literal/reference Add/Sub scope. The inspected individual packets contain no literal 1950 token. This does not establish that a 1950 transformation is impossible or absent from the unresolved shared definitions.

The 27 multiplication/addition expressions also carry 78 native `0x40` formatting/space attributes. The initial selector conservatively refused attributes using an over-specific internal reason name; the derived account corrects that description. These bytes supply no evidence of conditional logic. No native function calls were observed or executed. Multiplication can form an affine model, so refusal by this restricted selector is not proof that the source equations are non-affine.

The [token source account](age-formula-operators-source.json) preserves the exact original native report, private packet hashes, actual exit zero and twelve synthetic controls. All source/runtime pins remained unchanged. No formula, source age or calibration model was evaluated; no source age was converted. That initial inspection did not supply shared definitions or qualify multiplication. The later syntax follow-up below addresses those two limits while leaving source reference meaning, calibration, calendar conventions and intended use unresolved. The native `Sample age (cal AD/BC)` header remains a source assertion.

## Affine syntax and shared source definitions

The subsequent [affine structure account](age-formula-affine-structure.json) recovers **five SHRFMLA definitions** from the two retained source worksheet streams and binds all 36 shared-formula consumers to their exact same-sheet anchors and declared ranges. Together with 27 direct formulas, **all 63 formulas qualify affine syntax** under a bounded BIFF8 grammar. The new symbolic check accepts multiplication when one operand is a constant-only expression, plus addition, subtraction, unary signs and parentheses. It builds expression trees and resolves source cell addresses; it reads no referenced cell values and computes no source ages.

The 63 address comparisons match a separate pinned xlrd address helper exactly. Both methods share source bytes, xlrd and CompDoc provenance, so this is a parser correspondence check rather than independent source authentication. The run also passes 36 synthetic controls and 48 synthetic address comparisons. Unsupported operators, conditional attributes, external or named references, malformed records, ambiguous anchors and out-of-range consumers retain explicit refusal controls. No ARRAY record was observed in the two selected worksheets; other sources remain outside this follow-up.

Across the 63 qualified expansions, 156 `0x40` attributes are formatting/space and no literal 1950 token occurs. This neither establishes an epoch nor proves a different transformation impossible. The [source account](age-formula-affine-structure-source.json) retains exact producer, input, definition, expression and terminal hashes. Detailed formula constants, source addresses and record associations remain private. The initial inspection's 63 strict-template refusals remain unchanged as evidence for its earlier grammar; they are distinct from the new affine syntax qualification.

The actual native run returned zero without reading canonical original workbooks, loading cached cell grids, recalculating source values or repeating the full 79-workbook census. The native `Sample age (cal AD/BC)` header remains a source assertion. Qualifying reference units, chronology/model provenance, calibration, calendar/year-zero conventions, historical study selection and analytical-use rights still requires source evidence and independent review. Affine syntax does not establish age accuracy or authorize source-age conversion.

## Original archive members and complete worksheet layout

The new [archive/member account](archive-member-layout.json) compares the exact retained 509,919-byte `rootsi.7z` archive with the existing source roster. Native `bsdtar` lists **82 entries: one directory and 81 regular files**. Its 79 XLS members are streamed to stdout twice, once in each lane. Each lane contains **4,466,176 bytes**, and every member hash and size matches the retained workbook identity. No archive-named filesystem destinations are restored. The streamed XLS bytes are retained in 158 binary `.stdout` artifact logs; `file_extraction_to_filesystem=false` distinguishes those owned raw logs from restoring archive paths. The two extra regular files, a metadata OOXML workbook and an R script, are listed only; their bytes are neither inspected nor executed.

The maintained layout decoder then checks all **107 worksheets** in those 79 retained XLS files against the earlier sheet records. All are visible; 28 are empty. It scans **547,330 cached rectangle positions** for error types and observes no cached errors or merged ranges. This is a layout/error observation, not a recount of observed pollen grains, an authentication of source samples or an evaluation of formulas.

The report's `source_codepage_counts` field is **worksheet weighted**: 62 sheets carry codepage 1252 and 45 carry codepage 1200, totaling 107 sheets. These are not counts of 79 workbooks. The separate physical-record account above classifies 62 BIFF5/7 and 17 BIFF8 workbook-global headers; it uses a different denominator.

The [source and execution account](archive-member-layout-source.json) preserves the actual 161 native commands: one version query, two listings and 158 member streams, all returning zero. It binds the system tar binary, exact source roster, maintained module bytes, isolated interpreter and pinned xlrd 2.0.2 import. All 34,636 input pins remained unchanged. The first attempt completed both member-stream lanes but then failed because optional xlrd was unavailable; it remains a failed execution. The corrected successor's native exit is zero. Publication does not repeat either run.

This bounded comparison qualifies correspondence between one known archive and the retained member/layout records. It does not qualify a general adversarial 7z parser, malware or source-signature review, all-container security, historical scientific input selection, formula or chronology interpretation, or analytical-use rights. The complete archive-parser acceptance criterion remains open.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Retained four-workbook cell/layout preservation and the separate 79-workbook physical/formula accounts remain unchanged. A new bounded native comparison lists82 original archive entries and streams79 XLS members twice, matching4,466,176 bytes and every retained member identity per lane. Maintained layout/error inspection matches 107 sheets, including 28 empty sheets, all visible, with no merged ranges or cached errors.

**Unsupported claim.** General adversarial7z parser or malware/source-signature qualification, all-container security, source reference units or chronology/calibration accuracy, formula or source-code execution, historical study selection, observed grain counts, scientific-source approval and analytical/source-rights admission.

**Actual verification performed.** Original selected-cell stage 0 and retained focused checks unchanged. Raw 79-source successor native 0; independent on-demand workbook-global name/visibility/type/BOF/CODEPAGE checks load0 cached sheets;38 guards,Ruff/format,strict 2 pass;1530+85+runtime pins unchanged. Initial mixed-BOF refusal after48 books preserved. Retained63 packet/1131 token-byte inspection native 0 and 12 synthetic controls; all 63 strict 1950templates refused, no formula evaluation or cached age conversion. Subsequent two-artifact-source native 0 recovers 5 SHRFMLA definitions, qualifies 27 direct+36 shared affine expressions and matches 63 address-only oracle comparisons;36 synthetic controls/48 synthetic address comparisons pass. All 29 source/control and 3 runtime pins unchanged; no source cell evaluation or age conversion. Separate exact-original-archive successor native 0:161 native commands (1 version,2 listings,158 member streams),79 members per lane,107 worksheet layouts and 547,330 cached positions checked. All 34,636 input pins unchanged. Original missing-xlrd failure remains 1; successor explicitly pins xlrd 2.0.2. No prior BIFF/formula census rerun.

**Remaining input or review.** Known original archive-to-retained-member/layout correspondence is established for this exact source. Generic adversarial archive intake, malware/source-signature and complete-container security remain unqualified. Source units, calibration/calendar/model provenance, taxa/features, historical study selection and analytical-use authority remain unresolved. Resolver: LandClim workbook source custodian and independent archive, chronology and pollen-count reviewer Reopen when: New source evidence for general archive security/authenticity, historical study membership, reference units, derived-age/calibration/calendar semantics, taxa/units/chronology and analytical-use authority.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Retain exact original-archive/member correspondence and complete worksheet layout/error observations alongside earlier physical formula provenance. These boundaries do not establish source units, calibration, age accuracy, grain observations, historical study membership, general archive security or analytical-use authority.

**Precise next acceptance route.** Reuse the exact native archive/member/layout receipt and earlier cell, BIFF and affine-syntax receipts. Independently qualify adversarial archive intake, source signatures/security, historical selected membership, source reference units and chronology/calibration/calendar provenance, taxa/units and intended-use authority.

**Negative or refused result.** Original alias/parser/mixed-BOF failures and 63 initial strict 1950-template refusals remain retained. New bounded grammar qualifies63 affine syntaxes without endorsing source chronology; malformed/nonaffine/control/external/name/range/ambiguous-anchor cases refuse in controls. No literal 1950 in qualified expansions;156 formatting attributes are not conditional evidence. No general transform impossibility, source-age conversion or rights decision. New first archive attempt remains failed after successful stream lanes because optional xlrd was unavailable. No unsupported archive corpus or malicious input was tested; the two extra metadata/R members were only listed and not read or executed.

**Matched denominator.** New archive scope: 82 entries = 81 regular files + one directory; 79 XLS files + two listed-only regular members; two lanes of 79 streams and 4,466,176 bytes per lane. The layout pass covers 107 sheets, including 28 empty sheets, and 547,330 cached positions, with zero merged ranges and cached errors. Codepages are sheet weighted: 62 at 1252 + 45 at 1200 = 107 sheets. Earlier 79 workbook-global headers remain 62 BIFF5/7 + 17 BIFF8, including two mixed-header books; the separate physical pass has 54,419 records and 63 formula instances in two source-age columns. Earlier four-book preservation of 27,325 cells/eight sheets, the 5170−17=5153 row partition, and the two-worksheet/five-shared-definition syntax follow-up remain separate.

Retained evidence: [docs/report/source-relations/landclim/worksheet-layout/report.json](report.json), [docs/report/source-relations/landclim/worksheet-layout/source-account.json](source-account.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff.json](physical-biff.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff-source.json](physical-biff-source.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-operators.json](age-formula-operators.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-operators-source.json](age-formula-operators-source.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-affine-structure.json](age-formula-affine-structure.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-affine-structure-source.json](age-formula-affine-structure-source.json), [docs/report/source-relations/landclim/worksheet-layout/archive-member-layout.json](archive-member-layout.json), [docs/report/source-relations/landclim/worksheet-layout/archive-member-layout-source.json](archive-member-layout-source.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 7f4780aaf3d3e95520b23a619ccbfc1264def395336002af05411ed692344f63 -->
<!-- scientific-authored-source-sha256: 215015afb7bfac0bb5e45a121c51a6ea2eb0d38a370c0ca900949edc8712c080 -->
<!-- scientific-verification-and-limits:end -->
