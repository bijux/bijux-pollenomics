"""Reject ambiguous inputs before numerical execution or output creation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.api import LRARefusal
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request

from ..support import request_fixture


def test_source_hashes_and_canonical_request_remain_bound(tmp_path: Path) -> None:
    payload = request_fixture(tmp_path)
    accepted = validate_request(payload, input_root=tmp_path)
    assert accepted == validate_request(
        dict(reversed(list(payload.items()))), input_root=tmp_path
    )
    payload["taxa"][0] = "changed"
    assert accepted.payload()["taxa"] == ["Alnus", "Betula"]
    (tmp_path / "raw_snapshot.txt").write_text("changed source")
    with pytest.raises(LRARefusal) as raised:
        validate_request(accepted.payload(), input_root=tmp_path)
    assert raised.value.reason_code == "evidence_digest_mismatch"


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "absolute",
        "escape",
        "wrong_role",
        "duplicate",
        "unreported_uncertainty",
    ],
)
def test_invalid_evidence_is_a_reasoned_refusal(tmp_path: Path, kind: str) -> None:
    payload = request_fixture(tmp_path)
    if kind == "missing":
        (tmp_path / "raw_snapshot.txt").unlink()
    elif kind == "absolute":
        payload["evidence"][0]["path"] = str(tmp_path / "raw_snapshot.txt")
    elif kind == "escape":
        payload["evidence"][0]["path"] = "../outside.txt"
    elif kind == "wrong_role":
        payload["regional"]["samples"][0]["raw_evidence_id"] = "geometry"
    elif kind == "duplicate":
        payload["evidence"].append(deepcopy(payload["evidence"][0]))
    else:
        payload["uncertainty_omissions"] = []
    with pytest.raises(LRARefusal):
        validate_request(payload, input_root=tmp_path)


@pytest.mark.parametrize(
    "counts", [[0, 0], [0, None], [-1, 2], [1.5, 2], [True, 2], [1], [2**53, 1]]
)
def test_counts_preserve_zero_missing_and_exact_denominator(
    tmp_path: Path, counts: list[object]
) -> None:
    payload = request_fixture(tmp_path)
    payload["regional"]["samples"][0]["counts"] = counts
    with pytest.raises(LRARefusal):
        validate_request(payload, input_root=tmp_path)


def test_nonzero_totals_preserve_individual_zero_counts(tmp_path: Path) -> None:
    payload = request_fixture(tmp_path)
    payload["regional"]["samples"][0]["counts"] = [0, 10]
    assert validate_request(payload, input_root=tmp_path).payload()["regional"][
        "samples"
    ][0]["counts"] == [0, 10]


@pytest.mark.parametrize(
    "kind",
    [
        "fraction",
        "unknown_age",
        "backward_interval",
        "duplicate_coordinate",
        "different_bin",
        "different_site_geometry",
        "parameter_taxa",
        "ring_overlap",
        "same_site",
        "infinite_coordinate",
    ],
)
def test_method_input_semantics_cannot_be_silently_repaired(
    tmp_path: Path, kind: str
) -> None:
    payload = request_fixture(tmp_path, "series")
    row = payload["local"]["samples"][0]
    if kind == "fraction":
        payload["pollen_unit"] = "percentage"
    elif kind == "unknown_age":
        row["age_type"] = "radiocarbon_bp"
    elif kind == "backward_interval":
        row["age_support_bp"] = [[5600, 5400]]
    elif kind == "duplicate_coordinate":
        payload["local"]["samples"].append({**row, "sample_id": "new"})
    elif kind == "different_bin":
        row["bin_id"] = "another"
    elif kind == "different_site_geometry":
        payload["local"]["samples"].append(
            {**row, "sample_id": "new", "site_id": "another", "coordinate": 2}
        )
    elif kind == "parameter_taxa":
        payload["parameters"][0]["taxon"] = "unknown"
    elif kind == "ring_overlap":
        payload["rings"].append(
            {**payload["rings"][0], "inner_m": 150, "outer_m": 300, "mean_m": 250}
        )
    elif kind == "same_site":
        row["site_id"] = "regional-site"
    else:
        row["coordinate"] = float("inf")
    with pytest.raises(LRARefusal):
        validate_request(payload, input_root=tmp_path)


def test_disjoint_chronological_support_is_preserved_not_midpointed(
    tmp_path: Path,
) -> None:
    payload = request_fixture(tmp_path)
    payload["regional"]["samples"][0]["age_support_bp"] = [[100, 200], [500, 600]]
    payload["temporal_matching"]["bins"][0].update(younger_bp=100, older_bp=600)
    accepted = validate_request(payload, input_root=tmp_path).payload()["regional"][
        "samples"
    ][0]
    assert accepted["age_support_bp"] == [[100, 200], [500, 600]]
    assert accepted["coordinate"] == 1


@pytest.mark.parametrize("coordinate", [2**53 + 1, -(2**53 + 1)])
def test_integer_coordinate_cannot_lose_sample_identity(
    tmp_path: Path, coordinate: int
) -> None:
    payload = request_fixture(tmp_path)
    payload["regional"]["samples"][0]["coordinate"] = coordinate
    with pytest.raises(LRARefusal, match="regional-1") as error:
        validate_request(payload, input_root=tmp_path)
    assert error.value.reason_code == "inexact_pairing_coordinate"


@pytest.mark.parametrize(
    "kind",
    [
        "outside",
        "missing_bin",
        "reversed_bin",
        "duplicate_bin",
        "wrong_decision",
        "included_exclusion",
        "duplicate_exclusion",
    ],
)
def test_temporal_assumptions_and_sample_denominators_are_explicit(
    tmp_path: Path, kind: str
) -> None:
    payload = request_fixture(tmp_path)
    matching = payload["temporal_matching"]
    if kind == "outside":
        payload["regional"]["samples"][0]["age_support_bp"] = [[5000, 5500]]
    elif kind == "missing_bin":
        matching["bins"][0]["bin_id"] = "different"
    elif kind == "reversed_bin":
        matching["bins"][0].update(younger_bp=5600, older_bp=5400)
    elif kind == "duplicate_bin":
        matching["bins"].append(dict(matching["bins"][0]))
    elif kind == "wrong_decision":
        matching["decision_evidence_id"] = "geometry"
    elif kind == "included_exclusion":
        payload["exclusions"] = [
            {"sample_id": "regional-1", "reason_code": "not_eligible"}
        ]
    else:
        payload["exclusions"] = [
            {"sample_id": "excluded-1", "reason_code": "not_eligible"}
        ] * 2
    with pytest.raises(LRARefusal):
        validate_request(payload, input_root=tmp_path)
