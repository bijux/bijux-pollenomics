# Source worksheet layouts and cached values

The selected EKE, GIL, KRO_NY and RASH originals contain **eight worksheets**, all observed as visible. A source-bound sidecar now preserves each sheet's native visibility code, order, name, dimensions, merged ranges, character-decoding metadata and cached error codes. Hidden and very-hidden sheets are preserved by the contract; the selected originals contain neither. This is a four-workbook observation, not a census of all 79 workbooks.

The [account](report.json) retains **27,325 exact cached cell/type comparisons** and unchanged historical sheet-record hashes. The separate raw record comparison checks sixteen BOUNDSHEET name and visibility fields. KRO_NY uses the legacy BOF `0x0500` and codepage 1252; the other three originals use BOF `0x0600` and codepage 1200. Legacy ASCII sheet names and BIFF8 compressed Unicode names have different source layouts. The oracle reads those fields independently from the worksheet API while sharing xlrd's CompDoc container decoder. It does not recover every physical BIFF record or formula token.

All eight selected sheets have no decoded merged ranges or cached error cells. Four auxiliary sheets are empty and remain in the sidecar. These observations do not imply that other workbooks lack hidden sheets, merged cells, errors or external links. Source spelling is retained: ordinary roster selection refuses `KRO_ny.xls` when the captured member is `KRO_NY.xls`, including on a case-insensitive filesystem.

## Separate row and formula evidence

The earlier actual EKE consumer remains its original execution: all 1,376 cached values and types matched, and 42 mechanical rows partitioned into 25 positive-feature and seventeen zero-feature rows. Subtracting those seventeen from the retained 5,170 mechanical rows gives the metadata total of 5,153 under the declared row partition. Twenty-four positive EKE rows contain noninteger features. We did not repeat the other 78 workbooks' feature census or authenticate grain counts, interpolation, observed sample status or ecological absence.

Native XLS values in the selected sidecar are cached decoder outputs; that sidecar does not identify formula provenance. A separate physical-record account now locates formula records across all 79 retained workbooks, as described below. Their equations and derived-column meaning remain unreviewed, and no formula or source age is evaluated or converted. Formula cells and external-link parts in the separate OOXML metadata path remain subject to its maintained refusal contract. Archive membership remains bound to the historical receipt; these runs perform no fresh 7z extraction, malware scan or source-rights decision.

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

The physical pass finds **63 FORMULA records**: 36 in HAGG and 27 in KYLL, all in the second native column. The retained first-row header in both is `Sample age (cal AD/BC)`. These cached source age fields therefore have formula provenance. The equations, original inputs, calibration and age-model interpretation remain unreviewed; the run executes no formulas and silently converts no source ages. It makes no grain-count formula claim. Detailed record offsets, row/column associations and payload hashes remain private.

The inspected Workbook/Book streams contain no observed EXTERNNAME `0x0023`, EXTERNSHEET `0x0017` or SUPBOOK `0x01AE` records. This is a bounded record-presence statement; other compound-document streams, macro content, reference targets and security remain outside its scope. The parser refuses unsupported container extents, ambiguous stream aliases, truncated records, invalid flags and offsets, encrypted FILEPASS records, unsupported local headers and contradictory substream types.

A second source-pinned implementation uses xlrd's on-demand workbook-global parser to compare names, visibility, tab totals, BOF class and CODEPAGE. No cached worksheet is loaded. The two methods share xlrd's CompDoc container decoder, source bytes and interpreter. The actual successor returned zero with **38 focused controls**, configured Ruff and formatting, and strict typing of source and tests; all 1,530 source pins, 85 private-source pins and the runtime pin remained unchanged. The [physical source and execution account](physical-biff-source.json) preserves the failed predecessor, native outputs, independent global-field checks and exact maintained producer identities.

The maintained boundary is `bijux_pollenomics.collection.sources.rootsi.cells.biff.physical_biff_structure`. It accepts the pinned source bytes and pinned `xlrd.compdoc.CompDoc` decoder, returning a private record sidecar. For one already bound `WorkbookInput`, use `read_bytes(item.path, item.sha256, item.byte_count)` and pass those bytes to `physical_biff_structure`; this performs no cell-grid decoding. Keep that result in an owned private artifact destination. Original archive intake and scientific interpretation remain separate: this account assigns no taxonomy, pollen-count denominator, PPE, chronology probability, historical study membership or analytical-use rights.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Original four-book cached-value preservation remains27,325cells/eight sheets. A separate raw pass binds79original streams and107visible worksheet tabs,54,419physical records,63source-age FORMULA records and two mixed globals/sheet BOF sources without decoding cached rectangles.

**Unsupported claim.** Fresh original-archive intake/determinism, formula equation/calibration interpretation, all-CFB-stream security, external-target resolution, historical input authenticity, grain-count observations, scientific source or analytical-rights admission.

**Actual verification performed.** Original selected-cell stage0 and retained focused checks unchanged. Raw79-source successor native0; independent on-demand workbook-global name/visibility/type/BOF/CODEPAGE checks load0cached sheets;38guards,Ruff/format,strict2 pass;1530+85+runtime pins unchanged. Initial mixed-BOF refusal after48books preserved.

**Remaining input or review.** The complete retained79-workbook physical record layout and formula locations are now preserved. Source-age equations/calibration, archive intake, feature units, taxonomy, chronology interpretation, analytical rights and historical primary membership remain unresolved. Resolver: LandClim workbook source custodian and independent archive, chronology and pollen-count reviewer Reopen when: Source-qualified original archive and formula/derived-age semantics, authenticated row population, taxa/units/chronology and intended-use authority.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Retain physical formula provenance in source age fields and each substream header; source preservation alone cannot qualify calibration, native equations, grain counts, original study population or source-use authority.

**Precise next acceptance route.** Authenticate the original archive intake and formula-derived source age semantics/calibration, then qualify row populations, units/taxa/chronology, historical membership and rights. Reuse unchanged cached-cell receipts.

**Negative or refused result.** Original KRO_ny alias refusal and selected-oracle/test failures retained. Full raw predecessor refused RANV mixed BOF; supported local/global headers now preserved independently, unsupported grammar/type/offset still refuses.63formula-derived source-age values remain uninterpreted; no source-age conversion or rights decision.

**Matched denominator.** 79original4,466,176byte XLS inputs;107visible worksheet tabs;62BIFF5/7+17BIFF8 globals;2mixed-header books;54,419physical records;63FORMULA records in2source-age columns.0cached cells recounted. Original four-book27,325cells/8sheets/16fields and retained5170−17=5153 partition remain separate.

Retained evidence: [docs/report/source-relations/landclim/worksheet-layout/report.json](report.json), [docs/report/source-relations/landclim/worksheet-layout/source-account.json](source-account.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff.json](physical-biff.json), [docs/report/source-relations/landclim/worksheet-layout/physical-biff-source.json](physical-biff-source.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 14d5064c2eca17eff537f90c991fd7a104e91b54747f4894243051e46cf7aeca -->
<!-- scientific-authored-source-sha256: 7a94456651bd269154a81697fc48363b16d74c85ad1f89f7bb2a90baa9fcd0ef -->
<!-- scientific-verification-and-limits:end -->
