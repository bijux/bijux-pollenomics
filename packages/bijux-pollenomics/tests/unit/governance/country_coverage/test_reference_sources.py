"""Candidate-only EMPD2 and NFI country-coverage tests."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from typing import cast

import pytest

from bijux_pollenomics.governance.country_coverage import CountryCoverageError
from bijux_pollenomics.governance.country_coverage.constants import (
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    EMPD2_ASSIGNMENT_NOT_APPLIED,
    EMPD2_COVERAGE_EVIDENCE_PATH,
    EMPD2_SOURCE_ARTIFACT_SHA256,
    INPUT_PATHS,
    NFI_ASSIGNMENT_NOT_APPLIED,
    NFI_COVERAGE_EVIDENCE_PATH,
    NFI_SOURCE_ARTIFACT_SHA256,
)

from .fixtures import (
    _REPOSITORY_ROOT,
    _build,
    _cell,
    _cells,
    _counts,
    _replace_input_documents,
)

_PRE_REFERENCE_SOURCE_CELL_SHA256 = (
    "4d05ccfa114e08d3b7c8e0e1c2cd72b0a990a9ec876d17105aee1b350c9d2e8d"
)


def _reference_document_bytes(document: object) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _replace_reference_document(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    mutate: Callable[[dict[str, object]], None],
) -> None:
    document = cast(
        dict[str, object], json.loads((_REPOSITORY_ROOT / relative_path).read_bytes())
    )
    mutate(document)
    _replace_input_documents(
        monkeypatch,
        {relative_path: _reference_document_bytes(document)},
    )


def test_reference_source_manifests_are_canonical_and_appended_inputs() -> None:
    assert INPUT_PATHS[-2:] == (
        EMPD2_COVERAGE_EVIDENCE_PATH,
        NFI_COVERAGE_EVIDENCE_PATH,
    )
    assert len(INPUT_PATHS) == 20
    for relative_path in INPUT_PATHS[-2:]:
        payload = (_REPOSITORY_ROOT / relative_path).read_bytes()
        assert payload == _reference_document_bytes(json.loads(payload))


def test_reference_sources_preserve_existing_partitions() -> None:
    current = _cells(_build())

    def substantive(row: dict[str, object]) -> dict[str, object]:
        return {
            key: value
            for key, value in row.items()
            if key not in {"build_id", "config_digest"}
        }

    old_cells = [substantive(row) for row in current[:162]]
    old_cell_bytes = json.dumps(
        old_cells,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert hashlib.sha256(old_cell_bytes).hexdigest() == (
        _PRE_REFERENCE_SOURCE_CELL_SHA256
    )


def test_reference_source_cells_keep_candidates_out_of_admission() -> None:
    ledger = _build()
    assert ledger["source_family_count"] == 11
    assert ledger["cell_count"] == 198

    empd2 = {
        "SE": (132, 3_379, 131, 21),
        "DK": (20, 968, 20, 0),
        "NO": (622, 19_774, 622, 66),
        "FI": (141, 3_040, 141, 25),
    }
    for country, expected in empd2.items():
        cell = _cell(ledger, "empd2", "source_reported", country)
        counts = _counts(cell)
        assert (
            counts["received_records"],
            counts["observations"],
            counts["possible_candidates"],
            counts["unresolved_records"],
        ) == expected
        assert counts["samples"] == expected[0]
        assert cell["source_snapshot_id"] == f"sha256:{EMPD2_SOURCE_ARTIFACT_SHA256}"
        assert cell["lifecycle_status"] == "review_required"

    nfi = _cell(ledger, "nfi", "source_reported", "SE")
    assert (
        _counts(nfi)["received_records"],
        _counts(nfi)["sites"],
        _counts(nfi)["possible_candidates"],
        _counts(nfi)["unresolved_records"],
    ) == (43_892, 6_018, 16, 16)
    assert nfi["source_snapshot_id"] == f"sha256:{NFI_SOURCE_ARTIFACT_SHA256}"
    assert nfi["lifecycle_status"] == "review_required"

    methods = {
        "empd2": EMPD2_ASSIGNMENT_NOT_APPLIED,
        "nfi": NFI_ASSIGNMENT_NOT_APPLIED,
    }
    for source, method in methods.items():
        for dimension in COUNTRY_DIMENSIONS:
            for country in COUNTRIES:
                cell = _cell(ledger, source, dimension, country)
                assert cell["lifecycle_status"] != "admitted"
                if dimension != "source_reported":
                    assert cell["country_assignment_method"] == method
                    assert cell["boundary_artifact_digest"] is None
                    assert set(_counts(cell).values()) == {None}


def test_reference_source_access_postures_are_explicit() -> None:
    ledger = _build()
    assert {
        country: (
            _cell(ledger, "nfi", "source_reported", country)["availability_status"],
            _cell(ledger, "nfi", "source_reported", country)["lifecycle_status"],
        )
        for country in COUNTRIES
    } == {
        "SE": ("available_partial", "review_required"),
        "DK": ("blocked", "refused"),
        "NO": ("not_available_from_source", "unavailable"),
        "FI": ("available_not_collected", "review_required"),
        "UNASSIGNED": ("not_applicable", "not_required"),
        "OUTSIDE": ("not_applicable", "not_required"),
    }


@pytest.mark.parametrize(
    ("relative_path", "field", "message"),
    [
        (
            EMPD2_COVERAGE_EVIDENCE_PATH,
            "reviewed_record_count",
            "EMPD2 coverage evidence identity changed",
        ),
        (
            NFI_COVERAGE_EVIDENCE_PATH,
            "reviewed_record_count",
            "NFI coverage evidence identity changed",
        ),
    ],
)
def test_reference_source_review_denominator_mutation_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    field: str,
    message: str,
) -> None:
    def mutate(document: dict[str, object]) -> None:
        document[field] = cast(int, document[field]) - 1

    _replace_reference_document(monkeypatch, relative_path, mutate)
    with pytest.raises(CountryCoverageError, match=message):
        _build()


def test_reference_source_artifact_identity_mutation_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate(document: dict[str, object]) -> None:
        countries = cast(list[dict[str, object]], document["countries"])
        countries[0]["source_artifact_sha256"] = "0" * 64

    _replace_reference_document(monkeypatch, EMPD2_COVERAGE_EVIDENCE_PATH, mutate)
    with pytest.raises(CountryCoverageError, match="EMPD2 SE evidence changed"):
        _build()


def test_reference_source_noncanonical_manifest_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _REPOSITORY_ROOT / NFI_COVERAGE_EVIDENCE_PATH
    replacement = path.read_bytes().replace(b"{\n", b"{ \n", 1)
    _replace_input_documents(monkeypatch, {NFI_COVERAGE_EVIDENCE_PATH: replacement})
    with pytest.raises(CountryCoverageError, match="evidence is not canonical"):
        _build()
