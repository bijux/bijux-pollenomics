"""No source reads precede temporal selection; full components bind actual geometry."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    object_mapping,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence.admission import (
    admit_temporal_sources,
)

from ...experiments.test_inputs import store
from .support import fixture_payload, spec_from_payload


def test_no_pollen_needed_and_model_declaration_is_not_evidence_id(
    tmp_path: Path,
) -> None:
    payload = fixture_payload(tmp_path)
    spec = spec_from_payload(payload)
    for site in spec.older_experiment.sites:
        (tmp_path / site.raw.path).unlink()
    consumed: set[str] = set()
    result = admit_temporal_sources(
        spec, input_root=tmp_path, consumed_geometry=consumed
    )
    assert consumed == {site.record.record_id for site in spec.older_experiment.sites}
    assert result.decision.training_admission is not None
    assert result.as_dict()["source_age_authenticity"] == "not_verified"
    assert result.decision.plan.fold == spec.temporal_plan.fold
    copied = result.geometries()
    copied.clear()
    assert len(result.geometries()) == 4


def test_unusable_required_chronology_reads_nothing(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path), maximum_lead=400)
    consumed: set[str] = set()
    result = admit_temporal_sources(
        spec, input_root=tmp_path / "absent", consumed_geometry=consumed
    )
    assert result.decision.training_admission is None
    assert result.geometries() == {}
    assert consumed == set()
    assert (
        object_mapping(result.decision.as_dict()["denominators"], "denominators")[
            "training_records"
        ]
        == 3
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("age_support_bp", [[4900, 4999]]),
        ("age_support_bp", [[4900, 4950], [4950, 5000]]),
        ("age_support_bp", [[True, 5000]]),
        ("age_type", "radiocarbon_bp"),
        ("bin_id", "test-bin"),
        ("coordinate", 2**53 + 1),
    ],
)
def test_fully_rehashed_geometry_cannot_override_full_plan(
    tmp_path: Path, field: str, value: object
) -> None:
    payload = fixture_payload(tmp_path)
    target = payload["sites"][-1]
    geometry = json.loads((tmp_path / target["geometry"]["path"]).read_text())
    geometry["sample_metadata"][field] = value
    target["geometry"] = store(tmp_path, target["geometry"]["path"], geometry)
    with pytest.raises(ValidationRefusal):
        admit_temporal_sources(spec_from_payload(payload), input_root=tmp_path)


def test_failed_late_admission_retains_successful_geometry_tracker(
    tmp_path: Path,
) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    target = spec.older_experiment.sites[-1]
    (tmp_path / target.geometry.path).unlink()
    consumed: set[str] = set()
    with pytest.raises(ValidationRefusal):
        admit_temporal_sources(spec, input_root=tmp_path, consumed_geometry=consumed)
    assert consumed == {"p01", "p02", "p03"}


def test_required_anchor_does_not_override_frozen_priority(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    spec = replace(
        spec,
        temporal_plan=replace(
            spec.temporal_plan, required_regional_record_ids=("p02",)
        ),
    )
    with pytest.raises(ValidationRefusal, match="first eligible"):
        admit_temporal_sources(spec, input_root=tmp_path / "absent")


def test_hash_pinned_chronology_bytes_are_read(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    (tmp_path / "chronology.json").write_text("{}")
    with pytest.raises(ValidationRefusal, match="frozen reference"):
        admit_temporal_sources(spec, input_root=tmp_path)


def test_raw_source_cannot_be_relabelled_chronology_before_read(tmp_path: Path) -> None:
    payload = fixture_payload(tmp_path)
    chronology = payload["request_template"]["evidence"][0]
    chronology.update(payload["sites"][-1]["raw"])
    with pytest.raises(ValidationRefusal, match="chronology"):
        admit_temporal_sources(
            spec_from_payload(payload), input_root=tmp_path / "absent"
        )


def test_rehashed_retained_geometry_still_binds_original_bytes(tmp_path: Path) -> None:
    from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json

    result = admit_temporal_sources(
        spec_from_payload(fixture_payload(tmp_path)), input_root=tmp_path
    )
    geometry = result.geometries()
    target = object_mapping(geometry["p04"], "target")
    target["longitude"] = 90
    geometry["p04"] = target
    with pytest.raises(ValidationRefusal, match="p04"):
        replace(result, geometry_json=canonical_json(geometry))
    texts = json.loads(result.source_text_json)
    texts["p04"] = canonical_json(target)
    with pytest.raises(ValidationRefusal, match="p04"):
        replace(
            result,
            geometry_json=canonical_json(geometry),
            source_text_json=canonical_json(texts),
        )


def test_excluded_geometry_and_pollen_are_not_opened(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    chronology = tuple(
        replace(row, support=None) if row.record_id == "p03" else row
        for row in spec.temporal_plan.chronologies
    )
    spec = replace(
        spec, temporal_plan=replace(spec.temporal_plan, chronologies=chronology)
    )
    excluded = spec.older_experiment.sites[2]
    (tmp_path / excluded.geometry.path).unlink()
    for site in spec.older_experiment.sites:
        (tmp_path / site.raw.path).unlink()
    result = admit_temporal_sources(spec, input_root=tmp_path)
    assert set(result.geometries()) == {"p01", "p02", "p04"}
    assert result.decision.require_training_admission().excluded_record_ids == ("p03",)


def test_chronology_hash_declaration_cannot_override_evidence(tmp_path: Path) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    row = spec.temporal_plan.chronologies[-1]
    assert row.support is not None
    changed = replace(
        row, support=replace(row.support, chronology_manifest_sha256="c" * 64)
    )
    spec = replace(
        spec,
        temporal_plan=replace(
            spec.temporal_plan,
            chronologies=(*spec.temporal_plan.chronologies[:-1], changed),
        ),
    )
    with pytest.raises(ValidationRefusal, match="chronology"):
        admit_temporal_sources(spec, input_root=tmp_path)


def test_older_pairing_guard_is_still_required(tmp_path: Path) -> None:
    payload = fixture_payload(tmp_path)
    site = payload["sites"][1]
    geometry = json.loads((tmp_path / site["geometry"]["path"]).read_text())
    geometry["sample_metadata"]["coordinate"] = 9
    site["geometry"] = store(tmp_path, site["geometry"]["path"], geometry)
    with pytest.raises(ValidationRefusal, match="coordinate"):
        admit_temporal_sources(spec_from_payload(payload), input_root=tmp_path)
