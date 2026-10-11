"""Position-preserving decoded values and exact review partitions."""

from __future__ import annotations

from collections import Counter
import hashlib
import math

from .models import encoded, integer, refuse, text


def source_id(*parts: object) -> str:
    """Derive stable IDs from complete unnormalized source locators."""
    return hashlib.sha256(encoded(parts)).hexdigest()


def cell_record(
    *,
    workbook_id: str,
    sheet_ordinal: int,
    row: int,
    column: int,
    cell_type: int,
    value: object,
    xf_index: int | None,
) -> dict[str, object]:
    """Preserve decoded scalar identity, never infer a count, age or unit."""
    for label, number in (
        ("sheet", sheet_ordinal),
        ("row", row),
        ("column", column),
        ("cell_type", cell_type),
    ):
        integer(number, label)
    if xf_index is not None:
        integer(xf_index, "xf_index", minimum=-1)
    native: object = value
    binary64: str | None = None
    reason: str | None = None
    if cell_type in (0, 1, 6):
        text(value, "cell text", empty=True)
        if cell_type in (0, 6) and value != "":
            refuse("invalid_empty_value", repr(value))
    elif cell_type in (2, 3):
        if type(value) is not float:
            refuse("invalid_decoded_number", repr(value))
        binary64 = value.hex()
        if not math.isfinite(value):
            native = None
            reason = "nonfinite_decoded_number"
    elif cell_type in (4, 5):
        integer(value, "boolean/error payload")
        if cell_type == 4 and value not in (0, 1):
            refuse("invalid_boolean_payload", repr(value))
    else:
        if type(value) not in (str, int, float, bool, type(None)):
            refuse("unsupported_decoded_value", type(value).__name__)
        reason = "unsupported_cell_type"
        if type(value) is float:
            binary64 = value.hex()
            if not math.isfinite(value):
                native = None
    return {
        "cell_id": source_id(workbook_id, sheet_ordinal, row, column),
        "workbook_id": workbook_id,
        "sheet_ordinal": sheet_ordinal,
        "row": row,
        "column": column,
        "cell_type": cell_type,
        "decoded_value": native,
        "binary64_hex": binary64,
        "xf_index": xf_index,
        "refusal_reason": reason,
    }


def validate_cell(value: dict[str, object]) -> dict[str, object]:
    """Reconstruct a cell to reject contradictory retained representations."""
    native = value.get("decoded_value")
    binary64 = value.get("binary64_hex")
    if binary64 is not None:
        try:
            parsed = float.fromhex(text(binary64, "binary64_hex"))
        except ValueError as exc:
            refuse("invalid_binary64", str(exc))
        if parsed.hex() != binary64:
            refuse("noncanonical_binary64", str(binary64))
        if math.isfinite(parsed):
            if type(native) not in (int, float) or native != parsed:
                refuse("contradictory_number", repr(native))
        elif native is not None:
            refuse("contradictory_number", repr(native))
        native = parsed
    xf = value.get("xf_index")
    expected = cell_record(
        workbook_id=text(value.get("workbook_id"), "workbook_id"),
        sheet_ordinal=integer(value.get("sheet_ordinal"), "sheet_ordinal"),
        row=integer(value.get("row"), "row"),
        column=integer(value.get("column"), "column"),
        cell_type=integer(value.get("cell_type"), "cell_type"),
        value=native,
        xf_index=None if xf is None else integer(xf, "xf_index", minimum=-1),
    )
    if encoded(expected) != encoded(value):
        refuse("cell_representation_mismatch", str(value.get("cell_id")))
    return expected


class Accounting:
    """Count decoded cells without naming them observations or pollen mass."""

    def __init__(self) -> None:
        self.types: Counter[str] = Counter()
        self.numbers: Counter[str] = Counter()
        self.refusals: Counter[str] = Counter()
        self.workbooks = 0
        self.sheets = 0
        self.empty_sheets = 0

    def add(self, record: dict[str, object]) -> None:
        """Include every rectangle position, including explicit missing cells."""
        self.types[str(record["cell_type"])] += 1
        reason = record["refusal_reason"]
        if reason is not None:
            self.refusals[str(reason)] += 1
        if record["cell_type"] == 2:
            value = float.fromhex(text(record["binary64_hex"], "number"))
            self.numbers["number_cells"] += 1
            self.numbers["finite_cells"] += int(math.isfinite(value))
            self.numbers["zero_cells"] += int(value == 0)
            self.numbers["negative_cells"] += int(value < 0)
            self.numbers["integer_valued_cells"] += int(
                math.isfinite(value) and value.is_integer()
            )

    def as_dict(self) -> dict[str, object]:
        """Return complete mechanical partitions and explicit scientific refusal."""
        return {
            "workbooks": self.workbooks,
            "sheets": self.sheets,
            "empty_sheets": self.empty_sheets,
            "rectangle_positions": sum(self.types.values()),
            "cell_types": dict(sorted(self.types.items())),
            "numeric_cells_not_pollen_counts": dict(sorted(self.numbers.items())),
            "refused_cell_representations": dict(sorted(self.refusals.items())),
            "scientifically_admitted_observations": 0,
        }
