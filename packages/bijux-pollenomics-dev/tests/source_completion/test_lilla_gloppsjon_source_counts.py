"""Check source container refusals and exact target count accounting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen as study,
)
from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen_scoring as scoring,
)
from bijux_pollenomics_dev.source_completion import (
    nordic_direct_pollen as source,
)

REPOSITORY = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("payload", (None, [], "manifest"))
def test_scoring_manifest_requires_object(tmp_path: Path, payload: object) -> None:
    manifest = tmp_path / study.RELATIONAL / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    protocol = {"source_relational_manifest_sha256": source._sha(manifest)}
    with pytest.raises(ValueError, match="source manifest must be an object"):
        scoring._verify_scoring_source(tmp_path, protocol)


@pytest.mark.parametrize("payload", (None, [], "training"))
def test_training_profiles_require_object(
    monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    protocol, _ = study._protocol(REPOSITORY)
    monkeypatch.setattr(study, "_compressed_read", lambda _: payload)
    with pytest.raises(ValueError, match="training profiles must be an object"):
        study._training(REPOSITORY, protocol)


def test_source_count_rows_preserve_units_missingness_and_outside_axis_mass(
    tmp_path: Path,
) -> None:
    direct: dict[str, object] = {
        "sample_id": "sample:a",
        "source_element": "pollen",
        "source_element_type": "pollen",
        "source_unit": "NISP",
        "unit_family": "count",
        "detection_status": "reported_value",
        "source_reported_name": "Alnus",
        "source_value": 6,
    }
    rows = [
        direct,
        {**direct, "source_value": 4},
        {**direct, "source_reported_name": "outside-axis", "source_value": 7},
        {**direct, "source_value": 0},
        {**direct, "source_value": True},
        {**direct, "source_value": -1},
        {**direct, "source_unit": "percent", "source_value": 30},
        {**direct, "detection_status": "missing", "source_value": None},
        {**direct, "sample_id": "unselected-source-sample", "source_value": 100},
    ]
    part = tmp_path / "observations.json"
    part.write_text(
        json.dumps(
            {
                "source_snapshot_id": source.SOURCE_SNAPSHOT,
                "build_id": source.RELATIONAL_BUILD,
                "rows": rows,
            }
        ),
        encoding="utf-8",
    )
    manifest = {
        "surfaces": {
            "observations": {
                "parts": [{"path": part.name, "sha256": source._sha(part)}]
            }
        }
    }
    actual = scoring._target_sample_counts(tmp_path, manifest, ["sample:a", "sample:b"])
    expected_a: scoring._SampleCounts = {
        "native_nisp": 17,
        "counts": {**dict.fromkeys(source.TAXA, 0), "Alnus": 10},
        "direct_count_rows": 4,
        "other_observation_rows": 4,
    }
    assert actual["sample:a"] == expected_a
    assert actual["sample:b"] == {
        "native_nisp": 0,
        "counts": dict.fromkeys(source.TAXA, 0),
        "direct_count_rows": 0,
        "other_observation_rows": 0,
    }
    part.write_text("changed source", encoding="utf-8")
    with pytest.raises(ValueError, match="observation part changed after guard"):
        scoring._target_sample_counts(tmp_path, manifest, ["sample:a", "sample:b"])
