from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import bijux_pollenomics.analysis.fieldwork.land_use as land_use


def _target() -> land_use._Target:
    return land_use._Target(
        requested_name="Test",
        registry_name="Test",
        latitude=1.0,
        longitude=2.0,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Test.",
        coordinate_source="Test.",
    )


def test_spatial_and_temporal_helpers_resolve_facade_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distance_calls: list[dict[str, float]] = []
    canonical_calls: list[tuple[int, int]] = []

    def distance(**coordinates: float) -> float:
        distance_calls.append(coordinates)
        return 19.5

    def canonical(start: int, end: int) -> tuple[int, int]:
        canonical_calls.append((start, end))
        return (start, end)

    monkeypatch.setattr(land_use, "haversine_km", distance)
    monkeypatch.setattr(land_use, "canonical_bp_interval", canonical)
    monkeypatch.setattr(
        land_use, "closed_bp_intervals_overlap", lambda left, right: left == right
    )

    assert land_use._within_radius(_target(), latitude=3.0, longitude=4.0)
    assert land_use._intervals_overlap(0, 100, 0, 100)
    assert len(distance_calls) == 1
    assert canonical_calls == [(0, 100), (0, 100)]


def test_composite_helpers_resolve_facade_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(land_use, "_polygon_contains", lambda *args, **kwargs: True)
    feature: dict[str, object] = {
        "properties": {"dataset_id": land_use._LANDCLIM_DATASET_ID, "time_start_bp": 0},
        "geometry": {},
    }
    assert land_use._target_landclim_features(_target(), [feature]) == [feature]

    monkeypatch.setattr(land_use, "_within_radius", lambda *args, **kwargs: True)
    monkeypatch.setattr(land_use, "_intervals_overlap", lambda *args: True)
    result = land_use._overlapping_human_context(
        target=_target(),
        localities=(
            SimpleNamespace(
                coordinates=SimpleNamespace(latitude=0.0, longitude=0.0),
                chronology=SimpleNamespace(time_start_bp=0, time_end_bp=100),
                sample_count=2,
            ),
        ),
        time_start_bp=0,
        time_end_bp=100,
    )
    assert result == {"locality_count": 1, "sample_count": 2}


def test_json_helpers_resolve_the_facade_codec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    loads_calls: list[str] = []
    dumps_calls: list[tuple[dict[str, object], int]] = []

    class Codec:
        @staticmethod
        def loads(value: str) -> object:
            loads_calls.append(value)
            return {"features": []}

        @staticmethod
        def dumps(payload: dict[str, object], *, indent: int) -> str:
            dumps_calls.append((payload, indent))
            return "encoded"

    monkeypatch.setattr(land_use, "json", Codec)
    source = tmp_path / "source.json"
    target = tmp_path / "target.json"
    source.write_text(json.dumps({"features": ["ignored"]}), encoding="utf-8")

    assert land_use._load_features(source) == []
    land_use.write_sweden_land_use_synthesis_json(target, {"rows": []})
    assert loads_calls == ['{"features": ["ignored"]}']
    assert dumps_calls == [({"rows": []}, 2)]
    assert target.read_text(encoding="utf-8") == "encoded"


def test_target_selection_resolves_the_facade_target_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[dict[str, object]] = []
    target_type = land_use._Target

    def replacement(**values: object) -> land_use._Target:
        created.append(values)
        return target_type(**values)  # type: ignore[arg-type]

    monkeypatch.setattr(land_use, "_Target", replacement)
    candidate = SimpleNamespace(
        lake_name="Registry Lake", latitude=56.2, longitude=13.8
    )
    targets = land_use._synthesis_targets(
        SimpleNamespace(assessments=(SimpleNamespace(candidate=candidate),))
    )

    assert targets[0].requested_name == "Registry Lake"
    assert created[0]["coordinate_source"] == "official SVAR lake representative point"
