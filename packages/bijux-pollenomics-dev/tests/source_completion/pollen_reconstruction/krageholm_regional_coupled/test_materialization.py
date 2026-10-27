"""Selected sample support is measured source accounting, never a preset total."""

from typing import Any

import pytest

from .materialization import NAMES, support_totals
from .source_accounts import SMALL


def supports() -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (name, code): {
            "native_sample_count": index + 1,
            "source_support_sha256": "a" * 64,
        }
        for index, code in enumerate(SMALL)
        for name in NAMES
    }


def test_support_counts_derive_per_core_and_total_without_an_acceptance_constant() -> (
    None
):
    rows = supports()
    assert support_totals(rows) == {"BOKE": 6, "BUS": 12, "SOLSOE83": 18}
    rows[(NAMES[0], "BOKE")]["native_sample_count"] = 8
    assert support_totals(rows) == {"BOKE": 13, "BUS": 12, "SOLSOE83": 18}
    assert sum(support_totals(rows).values()) == 43


@pytest.mark.parametrize("count", [0, -1, True, 1.0, "1", None])
def test_sample_support_requires_literal_positive_integer(count: object) -> None:
    rows = supports()
    rows[(NAMES[0], "BOKE")]["native_sample_count"] = count
    with pytest.raises(ValueError):
        support_totals(rows)


@pytest.mark.parametrize(
    "corruption", ["missing_row", "foreign_row", "missing_hash", "invalid_hash"]
)
def test_sample_support_population_and_fingerprints_are_complete(
    corruption: str,
) -> None:
    rows = supports()
    if corruption == "missing_row":
        del rows[(NAMES[0], "BOKE")]
    elif corruption == "foreign_row":
        rows[("other", "BOKE")] = rows.pop((NAMES[0], "BOKE"))
    else:
        rows[(NAMES[0], "BOKE")]["source_support_sha256"] = (
            "" if corruption == "missing_hash" else "z" * 64
        )
    with pytest.raises(ValueError):
        support_totals(rows)
