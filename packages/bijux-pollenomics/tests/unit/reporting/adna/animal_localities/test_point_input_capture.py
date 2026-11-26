"""Animal point input bytes and absence remain bound to one capture."""

from hashlib import sha256
from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.atlas_candidates import point_inputs
from bijux_pollenomics.adna.species.definitions import build_species_support_matrix


def test_selected_point_bytes_survive_source_replacement(tmp_path: Path) -> None:
    root = tmp_path / "adna" / "species"
    root.mkdir(parents=True)
    species = [
        s.slug for s in build_species_support_matrix() if s.latin_name != "Homo sapiens"
    ]
    name = species[0]
    source = root / name / "normalized" / "locality_summaries.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(b'{"localities": []}')
    paths = point_inputs.ANIMAL_POINT_PATHS
    pins: dict[str, dict[str, str | None] | None] = dict.fromkeys(species)
    files: dict[str, str | None] = dict.fromkeys(paths)
    files["normalized/locality_summaries.json"] = sha256(
        source.read_bytes()
    ).hexdigest()
    pins[name] = files
    capture = point_inputs.capture_animal_point_inputs(tmp_path, pins)
    source.write_bytes(b'{"localities": ["replacement"]}')
    assert (
        capture.read(name, "normalized/locality_summaries.json")
        == b'{"localities": []}'
    )
    assert capture.read(name, "normalized/sample_records.json") is None
    assert capture.species_present(name) is True
    assert capture.species_present(species[1]) is False


def test_point_capture_refuses_missing_species_declaration(tmp_path: Path) -> None:
    (tmp_path / "adna" / "species").mkdir(parents=True)
    with pytest.raises(ValueError, match="species"):
        point_inputs.capture_animal_point_inputs(tmp_path, {})


def test_real_animal_bundle_reads_held_bytes_after_replacement(tmp_path: Path) -> None:
    import shutil

    from bijux_pollenomics.core.repository import repository_data_root
    from bijux_pollenomics.reporting.adna.animal_localities import (
        build_tracked_animal_atlas_bundle,
    )
    from bijux_pollenomics.reporting.adna.animal_localities.assembly import (
        build_tracked_animal_atlas_bundle_from_inputs,
    )

    retained = repository_data_root(__file__) / "adna" / "species"
    root = tmp_path / "data"
    species_root = root / "adna" / "species"
    species_root.mkdir(parents=True)
    pins: dict[str, dict[str, str | None] | None] = {}
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        source_root = retained / species.slug
        if not source_root.is_dir():
            pins[species.slug] = None
            continue
        (species_root / species.slug).mkdir()
        files: dict[str, str | None] = {}
        for path in point_inputs.ANIMAL_POINT_PATHS:
            source = source_root / path
            if source.is_file():
                destination = species_root / species.slug / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                files[path] = sha256(destination.read_bytes()).hexdigest()
            else:
                files[path] = None
        pins[species.slug] = files
    captured = point_inputs.capture_animal_point_inputs(root, pins)
    (tmp_path / "before").mkdir()
    baseline = build_tracked_animal_atlas_bundle(
        data_root=root, output_dir=tmp_path / "before", atlas_slug="animals"
    )
    assert baseline.point_layers
    shutil.rmtree(species_root)
    (tmp_path / "after").mkdir()
    held = build_tracked_animal_atlas_bundle_from_inputs(
        data_root=root,
        output_dir=tmp_path / "after",
        atlas_slug="animals",
        point_inputs=captured,
    )
    assert held.point_layers == baseline.point_layers
    assert held.localities == baseline.localities


@pytest.mark.parametrize(
    "mutation",
    ["digest", "missing", "symlink", "extra_species", "missing_file_declaration"],
)
def test_capture_refuses_source_or_presence_changes(
    tmp_path: Path, mutation: str
) -> None:
    root = tmp_path / "adna" / "species"
    root.mkdir(parents=True)
    species = [
        s.slug for s in build_species_support_matrix() if s.latin_name != "Homo sapiens"
    ]
    name = species[0]
    source = root / name / "normalized" / "locality_summaries.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"{}")
    pins: dict[str, dict[str, str | None] | None] = dict.fromkeys(species)
    files: dict[str, str | None] = dict.fromkeys(point_inputs.ANIMAL_POINT_PATHS)
    files["normalized/locality_summaries.json"] = sha256(
        source.read_bytes()
    ).hexdigest()
    pins[name] = files
    if mutation == "digest":
        source.write_bytes(b'{"changed":true}')
    elif mutation == "missing":
        source.unlink()
    elif mutation == "symlink":
        source.unlink()
        source.symlink_to(tmp_path / "target")
    elif mutation == "extra_species":
        (root / species[1]).mkdir()
    else:
        del files["normalized/sample_records.json"]
    with pytest.raises(ValueError):
        point_inputs.capture_animal_point_inputs(tmp_path, pins)


def test_copied_capture_context_cannot_fall_back_after_lease_ends(
    tmp_path: Path,
) -> None:
    from contextvars import copy_context

    root = tmp_path / "adna" / "species"
    root.mkdir(parents=True)
    pins = {
        s.slug: None
        for s in build_species_support_matrix()
        if s.latin_name != "Homo sapiens"
    }
    captured = point_inputs.capture_animal_point_inputs(tmp_path, pins)
    with point_inputs.use_animal_point_inputs(captured, tmp_path):
        copied = copy_context()
        assert point_inputs.selected_point_inputs() is captured
    assert point_inputs.selected_point_inputs() is None
    with pytest.raises(ValueError, match="expired"):
        copied.run(point_inputs.selected_point_inputs)


def test_direct_capture_constructor_cannot_claim_wrong_pin(tmp_path: Path) -> None:
    species = [
        s.slug for s in build_species_support_matrix() if s.latin_name != "Homo sapiens"
    ]
    buffers: dict[str, dict[str, bytes | None] | None] = dict.fromkeys(species)
    pins: dict[str, dict[str, str | None] | None] = dict.fromkeys(species)
    bodies: dict[str, bytes | None] = dict.fromkeys(point_inputs.ANIMAL_POINT_PATHS)
    files: dict[str, str | None] = dict.fromkeys(point_inputs.ANIMAL_POINT_PATHS)
    bodies["normalized/sample_records.json"] = b"{}"
    files["normalized/sample_records.json"] = "0" * 64
    buffers[species[0]] = bodies
    pins[species[0]] = files
    with pytest.raises(ValueError, match="digest"):
        point_inputs.AnimalPointInputs(tmp_path, buffers, pins)


def test_capture_scope_rejects_nesting_and_resets_on_failure(tmp_path: Path) -> None:
    (tmp_path / "adna" / "species").mkdir(parents=True)
    pins = {
        s.slug: None
        for s in build_species_support_matrix()
        if s.latin_name != "Homo sapiens"
    }
    captured = point_inputs.capture_animal_point_inputs(tmp_path, pins)
    with (
        pytest.raises(RuntimeError),
        point_inputs.use_animal_point_inputs(captured, tmp_path),
    ):
        with (
            pytest.raises(ValueError, match="bound context"),
            point_inputs.use_animal_point_inputs(captured, tmp_path),
        ):
            pass
        raise RuntimeError("failed publication")
    assert point_inputs.selected_point_inputs() is None


def test_missing_captured_review_does_not_fall_back_to_new_file(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.adna.animal_localities.review import (
        _load_dataset_review,
    )

    species = [
        s.slug for s in build_species_support_matrix() if s.latin_name != "Homo sapiens"
    ]
    species_root = tmp_path / "adna" / "species" / species[0]
    species_root.mkdir(parents=True)
    pins: dict[str, dict[str, str | None] | None] = dict.fromkeys(species)
    pins[species[0]] = dict.fromkeys(point_inputs.ANIMAL_POINT_PATHS)
    captured = point_inputs.capture_animal_point_inputs(tmp_path, pins)
    review = species_root / "reports" / "support_summary.json"
    review.parent.mkdir()
    review.write_text('{"dataset_review": {}}', encoding="utf-8")
    with (
        point_inputs.use_animal_point_inputs(captured, tmp_path),
        pytest.raises(FileNotFoundError),
    ):
        _load_dataset_review(species_root)


def test_capture_refuses_total_held_byte_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    species = [
        s.slug for s in build_species_support_matrix() if s.latin_name != "Homo sapiens"
    ]
    path = (
        tmp_path
        / "adna"
        / "species"
        / species[0]
        / "normalized"
        / "sample_records.json"
    )
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}")
    pins: dict[str, dict[str, str | None] | None] = dict.fromkeys(species)
    files: dict[str, str | None] = dict.fromkeys(point_inputs.ANIMAL_POINT_PATHS)
    files["normalized/sample_records.json"] = sha256(b"{}").hexdigest()
    pins[species[0]] = files
    monkeypatch.setattr(point_inputs, "_MAX_CAPTURE_BYTES", 1)
    with pytest.raises(ValueError, match="bytes exceed"):
        point_inputs.capture_animal_point_inputs(tmp_path, pins)


def test_public_atlas_uses_held_animal_point_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json
    import re
    import shutil
    from types import SimpleNamespace
    from typing import Any, cast

    from bijux_pollenomics.core.repository import repository_data_root
    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.adna.animal_localities import (
        build_tracked_animal_atlas_bundle,
    )
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.geography import infer_publication_scope
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    retained = repository_data_root(__file__) / "adna" / "species"
    root = tmp_path / "data"
    species_root = root / "adna" / "species"
    species_root.mkdir(parents=True)
    pins: dict[str, dict[str, str | None] | None] = {}
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        source_root = retained / species.slug
        if not source_root.is_dir():
            pins[species.slug] = None
            continue
        (species_root / species.slug).mkdir()
        files: dict[str, str | None] = {}
        for path in point_inputs.ANIMAL_POINT_PATHS:
            source = source_root / path
            if source.is_file():
                destination = species_root / species.slug / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                files[path] = sha256(destination.read_bytes()).hexdigest()
            else:
                files[path] = None
        pins[species.slug] = files
    capture = point_inputs.capture_animal_point_inputs(root, pins)
    (tmp_path / "expected").mkdir()
    expected = build_tracked_animal_atlas_bundle(
        data_root=root,
        output_dir=tmp_path / "expected",
        atlas_slug="nordic",
        geography_scope=infer_publication_scope(
            ("Denmark", "Finland", "Norway", "Sweden")
        ),
    )
    expected_features = {
        layer["key"]: layer["features"] for layer in expected.point_layers
    }
    assert expected_features
    shutil.rmtree(species_root)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts=dict.fromkeys(
                ("Denmark", "Finland", "Norway", "Sweden"), 0
            ),
            all_samples=(),
        ),
    )
    output = tmp_path / "map"
    service.generate_multi_country_map(
        tmp_path / "v66",
        ("Denmark", "Finland", "Norway", "Sweden"),
        output,
        "Nordic",
        "nordic",
        context_root=root,
        lake_inputs=SwedenLakeInputs(),
        animal_point_inputs=capture,
    )
    html = (output / "nordic_map.html").read_text()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match is not None
    rows = cast(
        list[dict[str, Any]],
        normalize_asset_inventory(json.loads(match.group(1))["assets"]),
    )
    observed: dict[str, list[Any]] = {}
    for row in rows:
        if row["domain"] != "nodes" or not row.get("layer_key", "").startswith(
            "animal-"
        ):
            continue
        chunk = decode_chunk_script(
            (output / row["path"]).read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row.get("decoded_byte_count"),
        )
        observed.setdefault(row["layer_key"], []).extend(
            cast(list[Any], chunk["features"])
        )
    assert observed == expected_features
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["animal_selected_point_inputs"] == capture.identity()


def test_public_atlas_rejects_animal_owner_bypass_and_preserves_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs

    root = tmp_path / "data"
    (root / "adna" / "species").mkdir(parents=True)
    pins = {
        s.slug: None
        for s in build_species_support_matrix()
        if s.latin_name != "Homo sapiens"
    }
    capture = point_inputs.capture_animal_point_inputs(root, pins)
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(country_sample_counts={}, all_samples=()),
    )
    monkeypatch.setattr(
        atlas_bundle, "build_tracked_animal_atlas_bundle", lambda **_: None
    )
    output = tmp_path / "map"
    output.mkdir()
    (output / "prior.txt").write_bytes(b"keep")
    with pytest.raises(ValueError, match="maintained animal owner"):
        service.generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            output,
            "Nordic",
            "nordic",
            context_root=root,
            lake_inputs=SwedenLakeInputs(),
            animal_point_inputs=capture,
        )
    assert (output / "prior.txt").read_bytes() == b"keep"
