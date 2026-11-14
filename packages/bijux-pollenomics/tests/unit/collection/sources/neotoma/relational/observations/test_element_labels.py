"""Source element review keeps label normalization and refusal reasons stable."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra.materialization.neotoma.series import (
    source_element_status,
)
from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
    is_native_pollen,
)


@pytest.mark.parametrize(
    ("element", "element_type", "expected"),
    [
        ("pollen", "pollen", "source_label_pollen"),
        (" Pollen ", "POLLEN", "source_label_pollen"),
        (None, "pollen", "source_element_missing"),
        ("pollen", None, "source_element_type_missing"),
        ("stomate", "pollen", "source_element_labels_disagree"),
        ("pollen", "stomate", "source_element_labels_disagree"),
        ("stomate", "stomate", "source_element_not_pollen"),
        ("pollen/spore", "pollen/spore", "source_element_not_pollen"),
    ],
)
def test_source_element_review_preserves_typed_label_pair(
    element: object, element_type: object, expected: str
) -> None:
    assert source_element_status(element, element_type) == expected


@pytest.mark.parametrize(
    ("element", "element_type", "expected"),
    [
        ("pollen", "pollen", True),
        (" Pollen ", "POLLEN", False),
        (None, "pollen", False),
        ("pollen", None, False),
        ("stomate", "pollen", False),
        ("pollen", "stomate", False),
        ("stomate", "stomate", False),
    ],
)
def test_native_pollen_admission_requires_literal_specimen_labels(
    element: object, element_type: object, expected: bool
) -> None:
    assert is_native_pollen(element, element_type) is expected
