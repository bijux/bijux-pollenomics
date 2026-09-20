"""Verify the bounded WHH05 author-example input reconstruction."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import cast

import pytest

from bijux_pollenomics_dev.essd_reproduction.one_site import (
    AUTHOR_COMMIT,
    OneSiteExampleError,
    build_whh05_one_site_slice,
    validate_host_basin_diameter,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SOURCE_ROOT = (
    REPOSITORY / "artifacts/v2/engine/multisite-audit/rmfyfe-landclimII-current/source"
)

JsonObject = dict[str, object]


def _object(value: object) -> JsonObject:
    assert isinstance(value, dict)
    return cast(JsonObject, value)


@pytest.fixture(scope="module")
def payload() -> JsonObject:
    return build_whh05_one_site_slice(SOURCE_ROOT).payload()


def test_slice_binds_every_historical_input_by_exact_identity(
    payload: JsonObject,
) -> None:
    source = _object(payload["source"])
    assert source["repository"] == "rmfyfe/landclimII"
    assert source["commit"] == AUTHOR_COMMIT
    assert source["archive_sha256"] == (
        "cd6cc688e6c44dd61d0ed038f53d118f4aade0696c37dc6174d613a38097bb38"
    )
    rows = cast(list[JsonObject], source["input_files"])
    observed = {cast(str, row["role"]): row for row in rows}
    expected_hashes = {
        "site_metadata": (
            "72949e9e3faf417be0b7425fc111a9638b37c4a38aab8f8d82e0c3d8739da2de"
        ),
        "raw_counts": (
            "977b32b96578aeb701288e77e37ab137e0475acd99274ddbdcc05180a8a99469"
        ),
        "prepared_counts": (
            "298b66d7033703ce42d27f933b4d3ccec3a16f68b35a6fbf7a61806c01c88273"
        ),
        "time_window_boundaries": (
            "62cac73bafacb8be8d8b7007e9871494024e661ab1a2f28774dcf7cb7046a71f"
        ),
        "time_window_lookup": (
            "888a2d5d035c8a49bd957917ca0658bb08824240ac15c1da4b717c633ddae3dd"
        ),
        "taxon_lookup": (
            "3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507"
        ),
        "ppe_means": (
            "066ebadbe6ab10aead80c74a184284e05b9db3cd1f5daff04249596170a663e2"
        ),
        "ppe_covariance": (
            "8821de94682c454e3a751897b487c8bf1612cf60994dc6246fb33284a73e9918"
        ),
        "historical_r_source": (
            "7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87"
        ),
    }
    assert set(observed) == set(expected_hashes)
    assert {
        role: cast(str, row["sha256"]) for role, row in observed.items()
    } == expected_hashes
    for row in rows:
        path = SOURCE_ROOT / cast(str, row["path"])
        assert path.stat().st_size == row["byte_count"]


def test_raw_sum_is_not_misreported_as_a_thirty_first_taxon(
    payload: JsonObject,
) -> None:
    denominators = _object(payload["denominators"])
    assert denominators == {
        "raw_named_taxa": 30,
        "raw_count_fields_including_declared_sum": 31,
        "prepared_taxa": 31,
        "raw_positive_named_taxa": 14,
        "prepared_positive_taxa": 10,
    }
    selection = _object(payload["selection"])
    raw = _object(selection["raw_observation"])
    assert raw["declared_sum_is_taxon"] is False
    assert raw["declared_sum"] == 301
    assert (raw["measurement_kind"], raw["is_percentage"]) == ("count", False)
    assert raw["source_locator"] == "input/WHH05.csv#age.cal.BP=1320"


def test_reconciliation_is_301_equals_297_plus_four_explicit_exclusions(
    payload: JsonObject,
) -> None:
    reconciliation = _object(payload["count_reconciliation"])
    assert reconciliation["raw_declared_total"] == 301
    assert reconciliation["prepared_total"] == 297
    assert reconciliation["explicit_exclusion_count"] == 4
    assert reconciliation["explicit_excluded_total"] == 4
    assert reconciliation["equation"] == (
        "301 raw = 297 prepared + 4 explicitly enumerated exclusions"
    )
    exclusions = cast(list[JsonObject], reconciliation["explicit_exclusions"])
    assert [(row["source_label_raw"], row["count"]) for row in exclusions] == [
        ("Centaurea nigra ", 1),
        ("Lactuceae  ", 1),
        ("Ranunculus acris type", 1),
        ("Potentilla type ", 1),
    ]
    assert all(row["ecological_judgment_asserted"] is False for row in exclusions)


def test_prepared_positive_counts_are_exact_and_not_percentages(
    payload: JsonObject,
) -> None:
    selection = _object(payload["selection"])
    prepared = _object(selection["prepared_observation"])
    assert prepared["positive_taxon_count"] == 10
    assert prepared["total_count"] == 297
    assert (prepared["measurement_kind"], prepared["is_percentage"]) == (
        "count",
        False,
    )
    assert prepared["positive_counts"] == {
        "Alnus.glutinosa": 2,
        "Betula": 1,
        "Calluna.vulgaris": 266,
        "Corylus.avellana": 4,
        "Cyperaceae": 2,
        "Ericaceae": 2,
        "Pinus": 1,
        "Plantago.lanceolata.type": 1,
        "Poaceae": 17,
        "Quercus.deciduous": 1,
    }


def test_source_age_stays_distinct_from_repository_bin_and_label(
    payload: JsonObject,
) -> None:
    selection = _object(payload["selection"])
    window = _object(selection["repository_time_window"])
    assert window == {
        "repository_window_id": 5,
        "younger_boundary_bp": 1250,
        "older_boundary_bp": 1750,
        "interval_notation": "[1250,1750)",
        "repository_window_label_bp": 1500,
        "source_age_cal_bp": 1320,
        "source_age_equals_window_label": False,
        "posture": (
            "source sample age is distinct from the repository bin support and label"
        ),
    }


def test_author_radius_is_converted_to_host_diameter_and_guarded(
    payload: JsonObject,
) -> None:
    selection = _object(payload["selection"])
    site = _object(selection["site"])
    assert site["author_radius_m"] == 150
    assert site["host_basin_diameter_m"] == 300
    assert site["author_radius_may_be_used_as_host_diameter"] is False
    validate_host_basin_diameter(source_radius_m=150, host_basin_diameter_m=300)
    with pytest.raises(OneSiteExampleError, match="expected 300, observed 150"):
        validate_host_basin_diameter(source_radius_m=150, host_basin_diameter_m=150)


def test_scope_and_historical_execution_do_not_overclaim(payload: JsonObject) -> None:
    assert payload["scope"] == "single_site_author_example_input_reconstruction"
    claims = _object(payload["claims"])
    assert claims == {
        "single_site_author_example_input_reconstructed": True,
        "whole_paper_reproduction": False,
        "rootsi_admission": False,
        "love_reconstruction": False,
        "multi_site_reconstruction": False,
        "native_r_parity": False,
        "ecological_accuracy": False,
        "publication_or_redistribution_rights_cleared": False,
        "scientifically_approved": False,
        "scientific_acceptance": "not_evaluated",
    }
    execution = _object(payload["historical_r_execution"])
    assert execution == {
        "performed": False,
        "bounded_inputs_authenticated": True,
        "isolated_private_diagnostic_call_technically_possible": True,
        "output_must_be_treated_as_unvalidated_candidate": True,
        "unchanged_unmanaged_historical_call_safe": False,
        "managed_isolation_preconditions": [
            "network disabled",
            "dependencies preinstalled and version-recorded",
            "historical source auto-install branches prevented",
            "outputs retained as private diagnostic candidates",
        ],
        "redistribution_or_publication_rights_cleared": False,
        "native_r_parity_certified": False,
        "historical_source_behavior_approved": False,
    }


def test_product_is_deterministic_and_payload_is_defensively_copied() -> None:
    first = build_whh05_one_site_slice(SOURCE_ROOT)
    second = build_whh05_one_site_slice(SOURCE_ROOT)
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256 == second.sha256
    assert json.loads(first.canonical_bytes) == first.payload()
    changed = first.payload()
    changed["scope"] = "mutated"
    assert first.payload()["scope"] == "single_site_author_example_input_reconstruction"


def test_any_input_drift_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "source"
    shutil.copytree(SOURCE_ROOT, copied)
    raw = copied / "input/WHH05.csv"
    content = raw.read_bytes()
    assert b",301\n" in content
    raw.write_bytes(content.replace(b",301\n", b",302\n", 1))
    with pytest.raises(OneSiteExampleError, match="pinned input identity mismatch"):
        build_whh05_one_site_slice(copied)
