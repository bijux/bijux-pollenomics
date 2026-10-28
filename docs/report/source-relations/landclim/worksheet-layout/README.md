# Source worksheet layouts and cached values

The selected EKE, GIL, KRO_NY and RASH originals contain **eight worksheets**, all observed as visible. A source-bound sidecar now preserves each sheet's native visibility code, order, name, dimensions, merged ranges, character-decoding metadata and cached error codes. Hidden and very-hidden sheets are preserved by the contract; the selected originals contain neither. This is a four-workbook observation, not a census of all 79 workbooks.

The [account](report.json) retains **27,325 exact cached cell/type comparisons** and unchanged historical sheet-record hashes. The separate raw record comparison checks sixteen BOUNDSHEET name and visibility fields. KRO_NY uses the legacy BOF `0x0500` and codepage 1252; the other three originals use BOF `0x0600` and codepage 1200. Legacy ASCII sheet names and BIFF8 compressed Unicode names have different source layouts. The oracle reads those fields independently from the worksheet API while sharing xlrd's CompDoc container decoder. It does not recover every physical BIFF record or formula token.

All eight selected sheets have no decoded merged ranges or cached error cells. Four auxiliary sheets are empty and remain in the sidecar. These observations do not imply that other workbooks lack hidden sheets, merged cells, errors or external links. Source spelling is retained: ordinary roster selection refuses `KRO_ny.xls` when the captured member is `KRO_NY.xls`, including on a case-insensitive filesystem.

## Separate row and formula evidence

The earlier actual EKE consumer remains its original execution: all 1,376 cached values and types matched, and 42 mechanical rows partitioned into 25 positive-feature and seventeen zero-feature rows. Subtracting those seventeen from the retained 5,170 mechanical rows gives the metadata total of 5,153 under the declared row partition. Twenty-four positive EKE rows contain noninteger features. We did not repeat the other 78 workbooks' feature census or authenticate grain counts, interpolation, observed sample status or ecological absence.

Native XLS values are cached decoder outputs. We neither recalculate formulas nor recover their origin or derived-column meaning. Formula cells and external-link parts in the separate OOXML metadata path remain subject to its maintained refusal contract. Native XLS external-link presence is not inspected by this sidecar. Archive membership remains bound to the historical receipt; this run performs no fresh 7z extraction, malware scan or source-rights decision.

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
