"""Historical SEAD admission keeps its own boundary authority."""

import hashlib
import json
from pathlib import Path

import pytest
from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    governed_sead_expected_identity,
)
from bijux_pollenomics.collection.sources.sead.collection import (
    repository_materialization,
)
from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.contract import (
    SEAD_NORMALIZED_LINEAGE_INPUTS,
    SEAD_NORMALIZED_LINEAGE_PATH,
)
from bijux_pollenomics.collection.sources.sead.collection.repository_surfaces.validation import (
    validate_normalized_lineage,
)
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
)


def test_governed_identity_accepts_explicit_historical_boundary_root(
    tmp_path: Path,
) -> None:
    current_data = tmp_path / "data"
    historical = tmp_path / "retained" / "boundaries"
    identity = governed_sead_expected_identity(
        current_data, historical_country_authority_root=historical
    )
    assert identity.country_authority_root == historical.resolve()
    assert (
        governed_sead_expected_identity(current_data).country_authority_root
        == (current_data / "boundaries").resolve()
    )


def test_v2_lineage_binds_historical_country_authority(tmp_path: Path) -> None:
    shared = {
        "source_run_id": "run",
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
    }
    hashes = {}
    for path in SEAD_NORMALIZED_LINEAGE_INPUTS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"{}")
        hashes[str(path.relative_to("sead"))] = hashlib.sha256(b"{}").hexdigest()
    review = tmp_path / "sead/review/temporal_review.json"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(json.dumps({"lineage": shared}))
    lineage = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        **shared,
        "acquisition_bundle_sha256": "bundle",
        "normalized_surface_sha256": hashes,
        "country_membership": {
            "purpose": "historical_admission_cohort",
            "authority_id": SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
            "artifact_digest": SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
        },
        "refresh_input_sha256": {
            **{
                f"boundary/{name}": "a" * 64
                for name in (
                    "raw/source_manifest.json",
                    "raw/sweden.geojson",
                    "raw/norway.geojson",
                    "raw/finland.geojson",
                    "raw/denmark.geojson",
                    "normalized/nordic_country_boundaries.geojson",
                )
            },
            "evidence/evidence_materialization_manifest.json": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
            "context/raa_density": None,
        },
    }
    lineage["refresh_input_sha256"][
        "boundary/normalized/nordic_country_boundaries.geojson"
    ] = SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST.removeprefix("sha256:")
    path = tmp_path / SEAD_NORMALIZED_LINEAGE_PATH
    path.write_text(json.dumps(lineage))
    validate_normalized_lineage(tmp_path)
    lineage["country_membership"]["artifact_digest"] = "sha256:" + "0" * 64
    captured_bad_lineage = json.dumps(lineage).encode()
    with pytest.raises(ValueError, match="country membership"):
        validate_normalized_lineage(tmp_path, lineage_bytes=captured_bad_lineage)
    path.write_text(json.dumps(lineage))
    with pytest.raises(ValueError, match="country membership"):
        validate_normalized_lineage(tmp_path)
    lineage["country_membership"]["artifact_digest"] = (
        SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST
    )
    del lineage["refresh_input_sha256"]["boundary/raw/finland.geojson"]
    path.write_text(json.dumps(lineage))
    with pytest.raises(ValueError, match="refresh input"):
        validate_normalized_lineage(tmp_path)
    lineage["refresh_input_sha256"]["boundary/raw/finland.geojson"] = "a" * 64
    lineage["refresh_input_sha256"][
        "boundary/normalized/nordic_country_boundaries.geojson"
    ] = "0" * 64
    path.write_text(json.dumps(lineage))
    with pytest.raises(ValueError, match="refresh input"):
        validate_normalized_lineage(tmp_path)


def test_historical_refresh_detects_changed_or_new_context(tmp_path: Path) -> None:
    historical = tmp_path / "historical"
    (historical / "raw").mkdir(parents=True)
    (historical / "normalized").mkdir()
    for name in (
        "source_manifest.json",
        "sweden.geojson",
        "norway.geojson",
        "finland.geojson",
        "denmark.geojson",
    ):
        (historical / "raw" / name).write_text(name)
    (historical / "normalized/nordic_country_boundaries.geojson").write_text("boundary")
    data = tmp_path / "data"
    evidence = (
        data / "sead/normalized/acquisitions" / "sead-full-evidence-39bfff6a-ce80714e"
    )
    evidence.mkdir(parents=True)
    (evidence / "evidence_materialization_manifest.json").write_text("evidence")
    snapshot = repository_materialization.capture_historical_refresh_inputs(
        data, historical
    )
    repository_materialization.require_historical_refresh_inputs_unchanged(
        data, historical, snapshot
    )
    raa = data / "raa/normalized/sweden_archaeology_density.geojson"
    raa.parent.mkdir(parents=True)
    raa.write_text("new context")
    with pytest.raises(RuntimeError, match="refresh input"):
        repository_materialization.require_historical_refresh_inputs_unchanged(
            data, historical, snapshot
        )


def test_historical_refresh_uses_captured_context_bytes(tmp_path: Path) -> None:
    historical = tmp_path / "historical"
    (historical / "raw").mkdir(parents=True)
    (historical / "normalized").mkdir()
    for name in (
        "source_manifest.json",
        "sweden.geojson",
        "norway.geojson",
        "finland.geojson",
        "denmark.geojson",
    ):
        (historical / "raw" / name).write_text(name)
    (historical / "normalized/nordic_country_boundaries.geojson").write_text("original")
    data = tmp_path / "data"
    context = data / "raa/normalized/sweden_archaeology_density.geojson"
    context.parent.mkdir(parents=True)
    context.write_text("original")
    staged = tmp_path / "staged"
    repository_materialization.stage_historical_refresh_inputs(data, historical, staged)
    context.write_text("replacement")
    (historical / "normalized/nordic_country_boundaries.geojson").write_text(
        "replacement"
    )
    assert (
        staged / "data/raa/normalized/sweden_archaeology_density.geojson"
    ).read_text() == "original"
    assert (
        staged / "boundaries/normalized/nordic_country_boundaries.geojson"
    ).read_text() == "original"


def test_historical_refresh_rejects_symlinked_boundary_directory(
    tmp_path: Path,
) -> None:
    source = tmp_path / "actual"
    source.mkdir()
    historical = tmp_path / "historical"
    historical.mkdir()
    (historical / "raw").symlink_to(source, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        repository_materialization.stage_historical_refresh_inputs(
            tmp_path / "data", historical, tmp_path / "staged"
        )
