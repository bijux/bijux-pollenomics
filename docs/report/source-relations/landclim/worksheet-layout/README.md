# Source worksheet layouts and cached values

The selected EKE, GIL, KRO_NY and RASH originals contain **eight worksheets**, all observed as visible. A source-bound sidecar now preserves each sheet's native visibility code, order, name, dimensions, merged ranges, character-decoding metadata and cached error codes. Hidden and very-hidden sheets are preserved by the contract; the selected originals contain neither. This is a four-workbook observation, not a census of all 79 workbooks.

The [account](report.json) retains **27,325 exact cached cell/type comparisons** and unchanged historical sheet-record hashes. The separate raw record comparison checks sixteen BOUNDSHEET name and visibility fields. KRO_NY uses the legacy BOF `0x0500` and codepage 1252; the other three originals use BOF `0x0600` and codepage 1200. Legacy ASCII sheet names and BIFF8 compressed Unicode names have different source layouts. The oracle reads those fields independently from the worksheet API while sharing xlrd's CompDoc container decoder. It does not recover every physical BIFF record or formula token.

All eight selected sheets have no decoded merged ranges or cached error cells. Four auxiliary sheets are empty and remain in the sidecar. These observations do not imply that other workbooks lack hidden sheets, merged cells, errors or external links. Source spelling is retained: ordinary roster selection refuses `KRO_ny.xls` when the captured member is `KRO_NY.xls`, including on a case-insensitive filesystem.

## Separate row and formula evidence

The earlier actual EKE consumer remains its original execution: all 1,376 cached values and types matched, and 42 mechanical rows partitioned into 25 positive-feature and seventeen zero-feature rows. Subtracting those seventeen from the retained 5,170 mechanical rows gives the metadata total of 5,153 under the declared row partition. Twenty-four positive EKE rows contain noninteger features. We did not repeat the other 78 workbooks' feature census or authenticate grain counts, interpolation, observed sample status or ecological absence.

Native XLS values in the selected sidecar are cached decoder outputs; that sidecar does not identify formula provenance. A separate physical-record account now locates formula records across all 79 retained workbooks, as described below. A later bounded account qualifies affine expression syntax and shared-definition bindings for these source age fields. Their source values, reference units, calibration and derived-age interpretation remain unqualified; no formula or source age is evaluated or converted. Formula cells and external-link parts in the separate OOXML metadata path remain subject to its maintained refusal contract. Archive membership remains bound to the historical receipt; these runs perform no fresh 7z extraction, malware scan or source-rights decision.

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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Original four-book preservation remains 27,325 cached cells/eight sheets. The separate raw pass binds79original streams/107visible worksheet tabs/54,419physical records/63source-age FORMULA records and two mixed-header sources. A bounded two-source follow-up recovers5shared definitions and qualifies affine syntax for63formulas (27direct/36shared), preserving same-sheet reference bindings without cell evaluation.

**Unsupported claim.** Source reference units, age-model/calibration interpretation or accuracy, epoch/calendar conversion, fresh original-archive intake/determinism, all-CFB-stream security, external-target resolution, historical input authenticity, grain-count observations, scientific source or analytical-rights admission.

**Actual verification performed.** Original selected-cell stage0 and retained focused checks unchanged. Raw79-source successor native0; independent on-demand workbook-global name/visibility/type/BOF/CODEPAGE checks load0cached sheets;38guards,Ruff/format,strict2 pass;1530+85+runtime pins unchanged. Initial mixed-BOF refusal after48books preserved. Retained63packet/1131token-byte inspection native0 and12synthetic controls; all63strict1950templates refused, no formula evaluation or cached age conversion. Subsequent two-artifact-source native0 recovers5SHRFMLA definitions, qualifies27direct+36shared affine expressions and matches63address-only oracle comparisons;36synthetic controls/48synthetic address comparisons pass. All29source/control and3runtime pins unchanged; no source cell evaluation or age conversion.

**Remaining input or review.** Complete retained79-workbook physical record layout and formula locations are preserved;63source-age expressions now have qualified affine syntax and same-sheet definition bindings. Referenced-value units, calibration/calendar/model provenance, archive intake, taxa/features, original study selection and analytical-use authority remain unresolved. Resolver: LandClim workbook source custodian and independent archive, chronology and pollen-count reviewer Reopen when: Source-qualified reference units and derived-age/calibration/calendar semantics, original archive and selected row population, taxa/units/chronology and intended-use authority.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Preserve source formula provenance, exact shared bindings and affine expression structure; syntax cannot qualify reference units, calibration, age accuracy, native chronology conversion, grain counts, original study population or analytical-use authority.

**Precise next acceptance route.** Independently review source reference units and chronology/model provenance, calibration/calendar conventions, original archive intake, historical selected membership and intended-use authority. Reuse unchanged cell/raw-record and newly qualified shared-definition syntax receipts.

**Negative or refused result.** Original alias/parser/mixed-BOF failures and63initial strict1950-template refusals remain retained. New bounded grammar qualifies63affine syntaxes without endorsing source chronology; malformed/nonaffine/control/external/name/range/ambiguous-anchor cases refuse in controls. No literal1950 in qualified expansions;156formatting attributes are not conditional evidence. No general transform impossibility, source-age conversion or rights decision.

**Matched denominator.** 79original4,466,176byte XLS inputs;107visible worksheet tabs;62BIFF5/7+17BIFF8 globals;2mixed-header books;54,419physical records;63FORMULA records in2source-age columns.0cached cells recounted. Original four-book27,325cells/8sheets/16fields and retained5170−17=5153 partition remain separate. New definition scope is2artifact source worksheets/5shared definitions/63formula instances (27direct+36shared),63reference comparisons;0cached grids loaded.

Retained evidence: [docs/report/source-relations/landclim/worksheet-layout/report.json](report.json), [docs/report/source-relations/landclim/worksheet-layout/source-account.json](source-account.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff.json](physical-biff.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff-source.json](physical-biff-source.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-operators.json](age-formula-operators.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-operators-source.json](age-formula-operators-source.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-affine-structure.json](age-formula-affine-structure.json), [docs/report/source-relations/landclim/worksheet-layout/age-formula-affine-structure-source.json](age-formula-affine-structure-source.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 5d10509e725a72f77113997ea1ed5c3f6776c8d6850ed174abad9820ade92c7a -->
<!-- scientific-authored-source-sha256: 1d2246faa0e556b13f5c173c81e679726864d2270b8cf0a1dcc8f5cb7f5d747f -->
<!-- scientific-verification-and-limits:end -->
