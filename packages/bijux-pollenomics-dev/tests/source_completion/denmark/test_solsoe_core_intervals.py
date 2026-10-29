"""Keep complete paper-interval proxies distinct from the historical unbounded calculation."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPLAY = "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py"


def load_source(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "solsoe_declared_core_intervals", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def source() -> ModuleType:
    return load_source(Path(__file__).resolve().parents[5] / REPLAY)


@pytest.mark.parametrize(
    ("core", "age", "expected"),
    [
        ("1981", -32, False),
        ("1981", -31, True),
        ("1981", -30, True),
        ("1981", 3489, True),
        ("1981", 3490, True),
        ("1981", 3491, False),
        ("1981", 7209, False),
        ("1981", 7210, True),
        ("1981", 7211, True),
        ("1981", 11649, True),
        ("1981", 11650, True),
        ("1981", 11651, False),
        ("1983", 3699, False),
        ("1983", 3700, True),
        ("1983", 3701, True),
        ("1983", 7179, True),
        ("1983", 7180, True),
        ("1983", 7181, False),
    ],
)
def test_complete_inclusive_endpoints(
    source: ModuleType, core: str, age: int, expected: bool
) -> None:
    identifier = source.CORE_1981 if core == "1981" else source.CORE_1983
    assert (
        source.closed_paper_interval_selected(
            {"collection_unit_id": identifier, "source_age_value": age}
        )
        is expected
    )


@pytest.mark.parametrize(
    "age", [None, True, False, "12417", float("nan"), float("inf")]
)
def test_invalid_source_age_refuses(source: ModuleType, age: object) -> None:
    with pytest.raises(ValueError):
        source.closed_paper_interval_selected(
            {"collection_unit_id": source.CORE_1981, "source_age_value": age}
        )


def test_excluded_oldest_native_age_keeps_legacy_distinction(
    source: ModuleType,
) -> None:
    # Raw source forensics bind neotoma:sample:353061 to 12417 calibrated BP.
    # This controlled age tests the predicate; it does not execute a 92-row replay.
    row = {"collection_unit_id": source.CORE_1981, "source_age_value": 12417}
    assert source.legacy_unbounded_selected(row) is True
    assert source.closed_paper_interval_selected(row) is False


def test_surface_endpoint_and_fraction_are_not_truncated(source: ModuleType) -> None:
    for age, expected in (
        (-31.0, True),
        (-31.1, False),
        (11650.0, True),
        (11650.1, False),
    ):
        assert (
            source.closed_paper_interval_selected(
                {"collection_unit_id": source.CORE_1981, "source_age_value": age}
            )
            is expected
        )


def test_unknown_core_refuses(source: ModuleType) -> None:
    with pytest.raises(ValueError):
        source.closed_paper_interval_selected(
            {"collection_unit_id": "other", "source_age_value": 5000}
        )


def test_declared_reference_interval_vectors(source: ModuleType) -> None:
    assert source.PAPER_INTERVALS_BP == {
        source.CORE_1981: ((-31, 3490), (7210, 11650)),
        source.CORE_1983: ((3700, 7180),),
    }


def test_central_point_does_not_classify_uncertainty_support(
    source: ModuleType,
) -> None:
    for identifier, center, younger, older, selected in (
        ("neotoma:sample:353061", 12417, 11495, 13410, False),
        ("neotoma:sample:353060", 11507, 11008, 12037, True),
    ):
        row = {
            "source_record_id": identifier,
            "collection_unit_id": source.CORE_1981,
            "source_age_value": center,
            "younger_bp": younger,
            "older_bp": older,
            "comparability_status": "comparable",
            "refusal_reason": None,
        }
        before = deepcopy(row)
        ledger = source.describe_proxy_row(row)
        assert ledger["closed_central_point_proxy_selected"] is selected
        assert ledger["source_record"] == before and row == before
        assert ledger["analytical_eligibility_evaluated"] is False
        assert ledger["lra_admitted"] is False


def test_refused_native_age_remains_refused_in_raw_proxy_ledger(
    source: ModuleType,
) -> None:
    row = {
        "source_record_id": "neotoma:sample:352996",
        "collection_unit_id": source.CORE_1981,
        "source_age_value": 7,
        "younger_bp": None,
        "older_bp": None,
        "source_age_younger": -41,
        "source_age_older": 60,
        "comparability_status": "refused",
        "refusal_reason": "negative_bp",
        "source_payload": {"age": 7, "ageyounger": -41, "ageolder": 60},
    }
    before = deepcopy(row)
    ledger = source.describe_proxy_row(row)
    assert ledger["closed_central_point_proxy_selected"] is True
    assert ledger["bounded_closed_central_point_proxy_selected"] is False
    assert ledger["source_record"] == before and row == before
    assert ledger["source_record"]["refusal_reason"] == "negative_bp"
    assert ledger["source_record"]["younger_bp"] is None
    assert ledger["source_record"]["older_bp"] is None
    assert ledger["source_record"]["source_age_younger"] == -41
    assert ledger["analytical_eligibility_evaluated"] is False
    assert ledger["lra_admitted"] is False
