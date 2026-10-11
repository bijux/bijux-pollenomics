"""Native labels and bounds never authorize geographic or temporal conversion."""

from dataclasses import asdict, replace

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowLimits,
    AsciiWindowSelection,
)
from bijux_pollenomics.collection.sources.hyde.ascii.reading import (
    selection_from_payload,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


@pytest.mark.parametrize(
    "field,value",
    [
        ("row_start", True),
        ("row_stop", 0),
        ("column_start", -1),
        ("column_stop", 0),
        ("member_index", False),
        ("archive_path", "../bad.zip"),
        ("native_labels", (("scenario", "invented"),)),
        ("native_labels", (("units", "base"),)),
        ("native_labels", (("scenario", "base"), ("scenario", "base"))),
    ],
)
def test_selection_refuses_malformed_indices_and_labels(
    field: str, value: object
) -> None:
    selection = AsciiWindowSelection("base.zip", 0, "a.asc", 0, 1, 0, 1)
    with pytest.raises(IntakeRefusal):
        selection_from_payload(
            {
                **asdict(selection),
                field: value,
                "native_labels": list(value)
                if field == "native_labels" and isinstance(value, tuple)
                else [],
            }
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("chunk_bytes", 0),
        ("maximum_source_cells", 10_000_001),
        ("maximum_token_bytes", True),
        ("maximum_member_bytes", -1),
    ],
)
def test_limits_are_bounded_positive_integers(field: str, value: int) -> None:
    with pytest.raises(IntakeRefusal):
        replace(AsciiWindowLimits(), **{field: value})


@pytest.mark.parametrize("role", [[], {}])
def test_direct_constructor_refuses_nontext_label_role(role: object) -> None:
    from typing import cast

    # Deliberately violate the public typed boundary; cast changes no runtime data.
    labels = ((cast(str, role), "base"),)
    with pytest.raises(IntakeRefusal):
        AsciiWindowSelection("base.zip", 0, "a.asc", 0, 1, 0, 1, labels)
