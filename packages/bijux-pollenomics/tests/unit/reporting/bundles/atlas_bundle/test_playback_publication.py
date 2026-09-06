"""Tests for atlas-owned playback storyboard publication."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from bijux_pollenomics.reporting.bundles.atlas_bundle import playback

from tests.unit.reporting.map_playback.support import modeled_manifest, source_layers


def _static_assets(*, classification_status: str = "unavailable") -> object:
    return SimpleNamespace(
        manifest={
            "build_id": "atlas-" + ("a" * 64),
            "scope_slug": "nordic",
            "version": "v66",
            "domains": {
                "classifications": {
                    "status": classification_status,
                    "reason_code": (
                        "accepted_scientific_classifications_not_available"
                        if classification_status == "unavailable"
                        else None
                    ),
                },
                "edges": {"record_count": 0},
            },
        }
    )


def test_nordic_publication_writes_identity_bound_storyboards(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        playback,
        "build_modeled_context_manifest",
        lambda _layers: modeled_manifest(),
    )
    output_path = tmp_path / "nordic_playback_storyboards.json"
    written: list[tuple[Path, dict[str, object]]] = []
    artifacts: list[tuple[str, str]] = []

    playback.publish_playback_storyboards(
        scope_key="nordic",
        countries=("Sweden", "Norway", "Finland", "Denmark"),
        bundle_paths=SimpleNamespace(playback_storyboards_path=output_path),
        point_layers=source_layers(),
        polygon_layers=[],
        static_assets=_static_assets(),
        extra_artifacts=artifacts,
        write_summary_json_fn=lambda path, payload: written.append((path, payload)),
    )

    assert len(written) == 1
    path, manifest = written[0]
    assert path == output_path
    assert manifest["atlas_identity"] == {
        "build_id": "atlas-" + ("a" * 64),
        "scope_slug": "nordic",
        "version": "v66",
        "countries": ["Denmark", "Finland", "Norway", "Sweden"],
    }
    assert manifest["source_chronology"]["story_count"] == 4
    assert manifest["modeled_context"]["story_count"] == 47
    assert artifacts == [
        (
            "Governed oldest-to-present playback storyboards",
            output_path.name,
        )
    ]


def test_broader_scopes_do_not_publish_nordic_only_storyboards(tmp_path: Path) -> None:
    written: list[object] = []
    artifacts: list[tuple[str, str]] = []

    playback.publish_playback_storyboards(
        scope_key="world",
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        bundle_paths=SimpleNamespace(
            playback_storyboards_path=tmp_path / "world_playback_storyboards.json"
        ),
        point_layers=[],
        polygon_layers=[],
        static_assets=object(),
        extra_artifacts=artifacts,
        write_summary_json_fn=lambda path, payload: written.append((path, payload)),
    )

    assert written == []
    assert artifacts == []


def test_candidate_storyboard_fails_closed_when_classifications_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        playback,
        "build_modeled_context_manifest",
        lambda _layers: modeled_manifest(),
    )

    with pytest.raises(ValueError, match="explicit unavailable classification"):
        playback.publish_playback_storyboards(
            scope_key="nordic",
            countries=("Denmark", "Finland", "Norway", "Sweden"),
            bundle_paths=SimpleNamespace(
                playback_storyboards_path=tmp_path / "nordic_playback_storyboards.json"
            ),
            point_layers=source_layers(),
            polygon_layers=[],
            static_assets=_static_assets(classification_status="available"),
            extra_artifacts=[],
            write_summary_json_fn=lambda _path, _payload: None,
        )
