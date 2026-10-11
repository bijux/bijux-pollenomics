from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde import load_declared_grid
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .fixtures import write_layer


def test_nodata_zero_source_values_and_unverified_release_are_distinct(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    assert layer.values == (0, 0.5, None, 1)
    assert layer.source_values == (0, 0.5, -9999, 1)
    assert layer.native_hyde_admission_verified is False
    assert layer.public_release_allowed is False
    assert layer.time.signed_bp_endpoints == (-50, -50)


def test_observed_digest_change_refuses_reuse(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    path = tmp_path / "layer.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(IntakeRefusal, match="digest_mismatch"):
        load_declared_grid(path, expected_sha256=layer.interchange_sha256)


def test_source_integer_values_remain_exact_and_population_rounding_refuses(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    assert type(layer.source_values[0]) is int
    assert type(layer.source_values[1]) is float
    declared_payload["variable"].update(quantity="population", units="persons")
    declared_payload["values"] = [[9007199254740993, 1], [None, 0]]
    with pytest.raises(IntakeRefusal, match="population_precision_loss"):
        write_layer(tmp_path, declared_payload)
    declared_payload["values"][0][0] = True
    with pytest.raises(IntakeRefusal, match="non_finite_number"):
        write_layer(tmp_path, declared_payload)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("nodata_value", 0, "nodata_overlaps"),
        ("values", [[True, 0], [0, 0]], "non_finite"),
        ("values", [[float("nan"), 0], [0, 0]], "non_finite"),
        ("values", [[1.1, 0], [0, 0]], "out_of_range"),
        ("values", [[0, 0]], "row_count"),
        ("land_fractions", [[None, 1], [1, 1]], "non_finite"),
        ("land_fractions", [[-1, 1], [1, 1]], "land_fraction_invalid"),
        ("land_fractions", [[1, 0], [1, 1]], "nonzero_value_on_water"),
    ],
)
def test_invalid_measure_or_mask_refuses(
    tmp_path: Path,
    declared_payload: dict[str, Any],
    field: str,
    value: Any,
    reason: str,
) -> None:
    declared_payload[field] = value
    with pytest.raises(IntakeRefusal, match=reason):
        write_layer(tmp_path, declared_payload)


def test_unconfirmed_native_format_and_older_release_are_refused(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    declared_payload["source"]["kind"] = "pre_normalized_candidate"
    declared_payload["source"]["release_claim"] = "3.2"
    with pytest.raises(IntakeRefusal, match="release_claim_unsupported"):
        write_layer(tmp_path, declared_payload)
    declared_payload["source"]["release_claim"] = "3.5"
    layer = write_layer(tmp_path, declared_payload)
    assert layer.native_hyde_admission_verified is False
    declared_payload["schema_version"] = "hyde-native-3.5"
    with pytest.raises(IntakeRefusal, match="native_format_unverified"):
        write_layer(tmp_path, declared_payload)


def test_units_and_category_spelling_cannot_be_silently_ignored(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    declared_payload["variable"]["units"] = "%"
    with pytest.raises(IntakeRefusal, match="quantity_units_unsupported"):
        write_layer(tmp_path, declared_payload)
    declared_payload["variable"]["units"] = "1"
    declared_payload["variable"]["category"] = "mistyped"
    with pytest.raises(IntakeRefusal, match="fields_invalid"):
        write_layer(tmp_path, declared_payload)


def test_size_limits_and_duplicate_json_keys_are_refused(
    tmp_path: Path, declared_payload: dict[str, Any]
) -> None:
    layer = write_layer(tmp_path, declared_payload)
    with pytest.raises(IntakeRefusal, match="size_limit"):
        load_declared_grid(
            tmp_path / "layer.json",
            expected_sha256=layer.interchange_sha256,
            maximum_bytes=10,
        )
    path = tmp_path / "duplicate.json"
    content = (
        json.dumps(declared_payload)
        .replace(
            '"schema_version":', '"schema_version": "duplicate", "schema_version":'
        )
        .encode()
    )
    path.write_bytes(content)
    with pytest.raises(IntakeRefusal, match="native_format_unverified"):
        load_declared_grid(path, expected_sha256=hashlib.sha256(content).hexdigest())
