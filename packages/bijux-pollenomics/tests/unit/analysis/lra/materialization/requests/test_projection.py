from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra.materialization.requests import (
    project_synthetic_neotoma_request,
)

from .fixture import projection_fixture


@contextmanager
def _refuses(reasons: str) -> Iterator[None]:
    with pytest.raises(LRARefusal) as raised:
        yield
    assert raised.value.reason_code in reasons.split("|")


def test_source_cells_zero_and_chronology_are_bound_into_portable_request(
    tmp_path: Path,
) -> None:
    inputs = projection_fixture(tmp_path)
    result = project_synthetic_neotoma_request(**inputs)
    request = json.loads((result.output_directory / "request.json").read_bytes())
    assert result.selected_samples == 2
    assert result.selected_cells == 4
    assert request["regional"]["samples"][0]["counts"] == [0, 100]
    assert request["local"]["samples"][0]["counts"] == [70, 30]
    assert request["regional"]["samples"][0]["age_support_bp"] == [[5400, 5600]]
    assert request["regional"]["samples"][0]["age_type"] == "calendar_bp"
    assert len(request["exclusions"]) == 7
    assert (
        validate_request(request, input_root=result.output_directory).sha256
        == result.request_sha256
    )
    manifest = json.loads((result.output_directory / "manifest.json").read_bytes())
    for item in manifest["artifacts"]:
        content = (result.output_directory / item["path"]).read_bytes()
        assert len(content) == item["size_bytes"]
        assert hashlib.sha256(content).hexdigest() == item["sha256"]
    lineage = json.loads((result.output_directory / "lineage.json").read_bytes())
    assert lineage["available_samples"] == 9
    assert lineage["available_observations"] == 18
    assert len(lineage["cells"]) == 4
    assert manifest["empirical_validation_status"] == "not_evaluated"
    inputs["output_directory"] = tmp_path / "repeated"
    repeated = project_synthetic_neotoma_request(**inputs)
    assert repeated.manifest_sha256 == result.manifest_sha256


@pytest.mark.parametrize(
    "source_options", [{"synthetic": False}, {"omitted_marker_part": 9}]
)
def test_template_cannot_relabel_real_or_partially_marked_source(
    tmp_path: Path, source_options: dict[str, object]
) -> None:
    inputs = projection_fixture(tmp_path, **source_options)
    assert inputs["request_template"]["data_kind"] == "synthetic"
    with _refuses("synthetic_source_origin_required"):
        project_synthetic_neotoma_request(**inputs)
    assert not inputs["output_directory"].exists()


@pytest.mark.parametrize("value", [None, True, -1, 0.5, 9007199254740993])
def test_invalid_count_is_never_filled_or_rounded(
    tmp_path: Path, value: object
) -> None:
    inputs = projection_fixture(tmp_path, first_value=value)
    with _refuses("source_cell_not_count|invalid_count_denominator"):
        project_synthetic_neotoma_request(**inputs)
    assert not inputs["output_directory"].exists()


def test_mixed_native_count_units_require_explicit_transform(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path, unit="number")
    with _refuses("incompatible_source_count_units"):
        project_synthetic_neotoma_request(**inputs)


def test_radiocarbon_claim_never_becomes_calendar_age(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path, age_type="Radiocarbon years BP")
    with _refuses("source_chronology_not_comparable"):
        project_synthetic_neotoma_request(**inputs)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reused", "wrong_owner"])
def test_cell_inventory_requires_exact_source_ownership(
    tmp_path: Path, mutation: str
) -> None:
    inputs = projection_fixture(tmp_path)
    cells = inputs["cell_bindings"]
    if mutation == "missing":
        cells.pop()
    elif mutation == "duplicate":
        cells.append(cells[0])
    elif mutation == "reused":
        cells[1] = replace(cells[1], observation_id=cells[0].observation_id)
    else:
        cells[0], cells[2] = (
            replace(cells[0], observation_id=cells[2].observation_id),
            replace(cells[2], observation_id=cells[0].observation_id),
        )
    with _refuses("source_cell_inventory_mismatch|source_cell_identity_mismatch"):
        project_synthetic_neotoma_request(**inputs)


def test_foreign_sample_chronology_binding_refuses(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path)
    claims = inputs["chronology_bindings"]
    claims[0] = replace(claims[0], chronology_claim_id=claims[1].chronology_claim_id)
    with _refuses("chronology_sample_ownership_mismatch"):
        project_synthetic_neotoma_request(**inputs)


def test_prefilled_counts_and_unaccounted_samples_refuse(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path)
    request = inputs["request_template"]
    request["regional"]["samples"][0]["counts"] = [1, 2]
    with _refuses("prefilled_derived_source_field"):
        project_synthetic_neotoma_request(**inputs)
    del request["regional"]["samples"][0]["counts"]
    request["exclusions"].pop()
    with _refuses("source_sample_denominator_mismatch"):
        project_synthetic_neotoma_request(**inputs)


def test_parameter_evidence_must_match_actual_parameter_values(tmp_path: Path) -> None:
    inputs = projection_fixture(tmp_path)
    inputs["request_template"]["parameters"][0]["ppe"] = 9
    with _refuses("fixture_declaration_mismatch"):
        project_synthetic_neotoma_request(**inputs)


def test_output_overlap_and_foreign_destination_refuse_before_writes(
    tmp_path: Path,
) -> None:
    inputs = projection_fixture(tmp_path)
    inputs["output_directory"] = inputs["raw_root"] / "bridge" / ".." / "nested"
    with pytest.raises(ValueError, match="overlap"):
        project_synthetic_neotoma_request(**inputs)
    assert not (inputs["raw_root"] / "nested").exists()
    output = tmp_path / "foreign"
    output.mkdir()
    (output / "keep").write_text("foreign")
    inputs["output_directory"] = output
    with pytest.raises(FileExistsError):
        project_synthetic_neotoma_request(**inputs)
    assert (output / "keep").read_text() == "foreign"
