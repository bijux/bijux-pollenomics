"""Only source-backed occupied cells and bound supplied reviews may be admitted."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority
from tests.support.context_data.raa import (
    REVIEW_INPUT_PATHS,
    geometry,
    grid_cell,
    inventory,
    read_json,
    write_authority_fixture,
    write_json,
    write_synthetic_review,
)


def test_legitimate_exclusions_reconcile_with_included_source_ids(
    tmp_path: Path,
) -> None:
    source = inventory(["Fornlämning"] * 6 + ["Möjlig fornlämning"])
    source["features"][2]["geometry"] = {"type": "Point", "coordinates": [18.5, 57.5]}
    source["features"][3]["geometry"] = {"type": "Point", "coordinates": [40, 70]}
    source["features"][4]["geometry"] = None
    source["features"][5]["geometry"] = {"type": "Point", "coordinates": []}
    shape = geometry()
    shape["coordinates"].append(
        [[18.4, 57.4], [18.6, 57.4], [18.6, 57.6], [18.4, 57.6], [18.4, 57.4]]
    )
    boundary = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"ADM0_A3": "SWE"}, "geometry": shape}
        ],
    }
    write_authority_fixture(tmp_path, source=source, boundary=boundary)
    decision = assess_raa_density_authority(tmp_path)
    assert decision.admitted
    assert decision.heritage_site_count == 6
    assert decision.density_site_count == 2


def test_public_class_totals_and_exact_case_density_selection_are_distinct(
    tmp_path: Path,
) -> None:
    source = inventory(["Fornlämning", " fornlämning ", "FORNLÄMNING", " Fornlämning "])
    write_authority_fixture(tmp_path, source=source)
    decision = assess_raa_density_authority(tmp_path)
    assert decision.admitted
    assert decision.heritage_site_count == 4
    assert decision.density_site_count == 2
    assert read_json(tmp_path / REVIEW_INPUT_PATHS["raw_inventory"]) == source


@pytest.mark.parametrize("empty", [True, False])
def test_zero_included_ids_are_not_unknown_population(
    tmp_path: Path, empty: bool
) -> None:
    source = inventory([] if empty else ["Fornlämning"])
    if not empty:
        source["features"][0]["geometry"] = None
    write_authority_fixture(tmp_path, source=source)
    decision = assess_raa_density_authority(tmp_path)
    assert decision.admitted
    assert decision.density_site_count == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "displaced",
        "duplicate",
        "count_bool",
        "coordinate_bool",
        "invalid_zero_geometry",
        "zero_coordinate_bool",
    ],
)
def test_equal_totals_cannot_hide_invalid_cell_geometry_or_identity(
    tmp_path: Path, mutation: str
) -> None:
    write_authority_fixture(tmp_path)
    path = tmp_path / REVIEW_INPUT_PATHS["normalized_density"]
    density = read_json(path)
    if mutation == "displaced":
        density["features"][0]["geometry"] = geometry(0, 0, 1, 1)
    elif mutation == "duplicate":
        density["features"].append(grid_cell(18, 57, 0))
    elif mutation == "count_bool":
        density["features"][0]["properties"]["count"] = True
    elif mutation == "coordinate_bool":
        density["features"][0]["geometry"]["coordinates"][0][0][0] = True
    elif mutation == "invalid_zero_geometry":
        density["features"].append(
            {"type": "Feature", "geometry": None, "properties": {"count": 0}}
        )
    else:
        zero = grid_cell(0, 0, 0)
        zero["geometry"]["coordinates"][0][0][0] = False
        density["features"].append(zero)
    write_json(path, density)
    metadata_path = tmp_path / REVIEW_INPUT_PATHS["normalized_metadata"]
    metadata = read_json(metadata_path)
    metadata["density_feature_count"] = len(density["features"])
    write_json(metadata_path, metadata)
    write_synthetic_review(tmp_path)
    assert not assess_raa_density_authority(tmp_path).admitted


@pytest.mark.parametrize("role", list(REVIEW_INPUT_PATHS))
def test_semantically_equal_bytes_still_require_a_current_review_receipt(
    tmp_path: Path, role: str
) -> None:
    write_authority_fixture(tmp_path)
    path = tmp_path / REVIEW_INPUT_PATHS[role]
    path.write_bytes(path.read_bytes() + b"\n")
    if role == "sweden_boundary":
        from tests.support.context_data.boundaries import (
            write_synthetic_boundary_manifest,
        )

        write_synthetic_boundary_manifest(tmp_path / "boundaries/raw")
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert "density_review_receipts_mismatch" in decision.reason_codes


@pytest.mark.parametrize("reviewer", [None, True, 42, {}, " "])
def test_reviewer_identity_requires_an_explicit_nonblank_string(
    tmp_path: Path, reviewer: object
) -> None:
    write_authority_fixture(tmp_path)
    path = tmp_path / "raa/review/spatiotemporal_review.json"
    review = read_json(path)
    review["reviewer_id"] = reviewer
    write_json(path, review)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert "scientific_review_not_accepted" in decision.reason_codes


@pytest.mark.parametrize(
    "mutation",
    [
        "native_id",
        "disposition",
        "count_bool",
        "record_missing",
        "raw_pin",
        "profile",
        "policy",
        "semantic_pin",
    ],
)
def test_bound_review_does_not_authorize_a_fabricated_membership_ledger(
    tmp_path: Path, mutation: str
) -> None:
    write_authority_fixture(tmp_path)
    path = tmp_path / REVIEW_INPUT_PATHS["membership_ledger"]
    ledger = read_json(path)
    if mutation == "native_id":
        ledger["records"][0]["native_id"] = "invented"
    elif mutation == "disposition":
        ledger["records"][0]["disposition"] = "excluded_source_class"
    elif mutation == "count_bool":
        ledger["counts"]["included"] = True
    elif mutation == "record_missing":
        ledger["records"].pop()
    elif mutation == "raw_pin":
        ledger["raw_inventory_identity"]["sha256"] = "0" * 64
    elif mutation == "profile":
        ledger["schema_version"] = "unknown"
    elif mutation == "policy":
        ledger["selection_policy"] = "unreviewed"
    else:
        ledger["semantic_payload_identity"]["sweden_boundary_sha256"] = "0" * 64
    write_json(path, ledger)
    write_synthetic_review(tmp_path)
    assert not assess_raa_density_authority(tmp_path).admitted


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_profile",
        "unknown_profile",
        "policy",
        "missing_receipt",
        "extra_receipt",
        "path",
        "sha",
        "count_bool",
    ],
)
def test_an_accepted_reviewer_string_cannot_replace_exact_input_receipts(
    tmp_path: Path, mutation: str
) -> None:
    write_authority_fixture(tmp_path)
    path = tmp_path / "raa/review/spatiotemporal_review.json"
    review = read_json(path)
    if mutation == "missing_profile":
        del review["schema_version"]
    elif mutation == "unknown_profile":
        review["schema_version"] = "unknown"
    elif mutation == "policy":
        review["selection_policy"] = "unreviewed"
    elif mutation == "missing_receipt":
        del review["input_artifacts"]["membership_ledger"]
    elif mutation == "extra_receipt":
        review["input_artifacts"]["arbitrary"] = {"path": "/no/opens"}
    else:
        review["input_artifacts"]["raw_inventory"][
            {"path": "path", "sha": "sha256", "count_bool": "byte_count"}[mutation]
        ] = {"path": "/no/opens", "sha": "0" * 64, "count_bool": True}[mutation]
    write_json(path, review)
    assert not assess_raa_density_authority(tmp_path).admitted
