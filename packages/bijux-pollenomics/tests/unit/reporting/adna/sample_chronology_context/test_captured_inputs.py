"""Chronology consumers use exact caller-pinned bytes and explicit absence."""

from hashlib import sha256
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics.core.filesystem import BoundedInputTree
from bijux_pollenomics.reporting.adna import sample_chronology_context as owner
from bijux_pollenomics.reporting.adna.sample_chronology_context import (
    captured_inputs,
    repository,
)

from .support import write_source_repository


def test_held_chronology_survives_source_replacement(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    source = tmp_path / "adna/governance/source_library"
    paths = [
        source / "project_registry.json",
        *sorted((source / "projects").glob("*/*.json")),
    ]
    pins = {
        path.relative_to(source).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    baseline = repository.load_animal_sample_chronology_corpus(tmp_path)
    held = captured_inputs.capture_animal_chronology_inputs(tmp_path, pins)
    shutil.rmtree(source)
    projection = repository.load_animal_sample_chronology_corpus(
        tmp_path, chronology_inputs=held
    )
    assert projection == baseline


def test_explicit_absence_does_not_discover_later_registry(tmp_path: Path) -> None:
    held = captured_inputs.capture_animal_chronology_inputs(tmp_path, None)
    write_source_repository(tmp_path)
    assert owner.animal_sample_chronology_context_available(tmp_path)
    assert not owner.animal_sample_chronology_context_available(
        tmp_path, chronology_inputs=held
    )


@pytest.mark.parametrize(
    "mutation",
    ["digest", "missing", "extra_project", "symlink", "missing_pin", "registry"],
)
def test_capture_refuses_changed_project_inventory(
    tmp_path: Path, mutation: str
) -> None:
    write_source_repository(tmp_path)
    source = tmp_path / "adna/governance/source_library"
    paths = [
        source / "project_registry.json",
        *sorted((source / "projects").glob("*/*.json")),
    ]
    pins = {
        path.relative_to(source).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    target = source / "projects/PRJTEST1/sample_chronology.json"
    if mutation == "digest":
        target.write_bytes(b"{}")
    elif mutation == "missing":
        target.unlink()
    elif mutation == "extra_project":
        (source / "projects/EXTRA").mkdir()
    elif mutation == "symlink":
        target.unlink()
        target.symlink_to(source / "project_registry.json")
    elif mutation == "missing_pin":
        del pins["projects/PRJTEST1/sample_sites.json"]
    else:
        (source / "project_registry.json").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        captured_inputs.capture_animal_chronology_inputs(tmp_path, pins)


def test_direct_constructor_rejects_unverified_bodies(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    source = tmp_path / "adna/governance/source_library"
    paths = [
        source / "project_registry.json",
        *sorted((source / "projects").glob("*/*.json")),
    ]
    bodies = {path.relative_to(source).as_posix(): path.read_bytes() for path in paths}
    pins = {name: sha256(body).hexdigest() for name, body in bodies.items()}
    pins["projects/PRJTEST1/sample_sites.json"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        captured_inputs.AnimalChronologyInputs(tmp_path, bodies, pins)


def test_absence_refuses_symlink_ancestor(tmp_path: Path) -> None:
    (tmp_path / "adna").symlink_to(tmp_path / "missing", target_is_directory=True)
    with pytest.raises(ValueError, match="directory"):
        captured_inputs.capture_animal_chronology_inputs(tmp_path, None)


def test_direct_absent_constructor_refuses_existing_registry(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    with pytest.raises(ValueError, match="presence"):
        captured_inputs.AnimalChronologyInputs(tmp_path, None, None)


def test_capture_refuses_registry_change_while_projects_are_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_source_repository(tmp_path)
    source = tmp_path / "adna/governance/source_library"
    paths = [
        source / "project_registry.json",
        *sorted((source / "projects").glob("*/*.json")),
    ]
    pins = {
        path.relative_to(source).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    real_read = BoundedInputTree.read
    altered = False

    def read_and_replace(
        tree: BoundedInputTree, path: Path, *, max_bytes: int | None = None
    ) -> bytes:
        nonlocal altered
        body = real_read(tree, path, max_bytes=max_bytes)
        if not altered:
            (source / "project_registry.json").write_bytes(b"{}")
            altered = True
        return body

    monkeypatch.setattr(BoundedInputTree, "read", read_and_replace)
    with pytest.raises(ValueError, match="registry changed"):
        captured_inputs.capture_animal_chronology_inputs(tmp_path, pins)


@pytest.mark.parametrize("present", [False, True])
def test_public_atlas_uses_held_chronology_with_aadr_and_animal_points(
    tmp_path: Path, present: bool
) -> None:
    import json
    import re
    from typing import Any, cast

    from bijux_pollenomics.adna.governance.atlas_candidates.point_inputs import (
        capture_animal_point_inputs,
    )
    from bijux_pollenomics.adna.species.definitions import build_species_support_matrix
    from bijux_pollenomics.adna.species.homo_sapiens import (
        build_homo_sapiens_runtime_manifest_for_version_dir,
    )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        capture_aadr_map_snapshot,
    )
    from bijux_pollenomics.core.repository import repository_data_root
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.geography import infer_publication_scope
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )
    from bijux_pollenomics.reporting.service import generate_multi_country_map
    from tests.support.aadr import write_anno_file

    root = tmp_path / "context"
    (root / "adna/species").mkdir(parents=True)
    point_pins = {
        s.slug: None
        for s in build_species_support_matrix()
        if s.latin_name != "Homo sapiens"
    }
    points = capture_animal_point_inputs(root, point_pins)
    scope = infer_publication_scope(("Sweden", "Norway"))
    expected: dict[str, object] = {}
    if present:
        source = repository_data_root(__file__) / "adna/governance/source_library"
        registry = json.loads((source / "project_registry.json").read_bytes())
        projects = [row["project_accession"] for row in registry["rows"]]
        names = ["project_registry.json"] + [
            f"projects/{project}/{name}"
            for project in projects
            for name in (
                "sample_master.json",
                "sample_chronology.json",
                "sample_sites.json",
            )
        ]
        target = root / "adna/governance/source_library"
        pins = {}
        for name in names:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, destination)
            pins[name] = sha256(destination.read_bytes()).hexdigest()
        expected_projection = owner.build_animal_sample_chronology_context(
            root, geography_scope=scope
        )
        expected = {
            cast(str, layer["key"]): layer["features"]
            for layer in expected_projection.point_layers
        }
        held = captured_inputs.capture_animal_chronology_inputs(root, pins)
        shutil.rmtree(target)
    else:
        held = captured_inputs.capture_animal_chronology_inputs(root, None)
        path = root / "adna/governance/source_library/project_registry.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"invalid registry must not be read")
    anno = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        anno, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(anno.parent.parent)
    aadr = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": sha256(anno.read_bytes()).hexdigest()}
    )
    anno.write_bytes(anno.read_bytes().replace(b"Sweden", b"Norway"))
    output = tmp_path / "map"
    report = generate_multi_country_map(
        anno.parent.parent,
        ("Sweden", "Norway"),
        output,
        "Nordic",
        "nordic",
        context_root=root,
        lake_inputs=SwedenLakeInputs(),
        animal_point_inputs=points,
        aadr_map_snapshot=aadr,
        animal_chronology_inputs=held,
    )
    assert report.country_sample_counts == {"Sweden": 1, "Norway": 0}
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["animal_chronology_inputs"] == held.identity()
    assert contract["animal_selected_point_inputs"] == points.identity()
    assert contract["aadr_map_annotation_inputs"] == aadr.identity()
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
    layer_keys: set[str] = set()
    for row in rows:
        if row["domain"] == "provenance":
            provenance = decode_chunk_script(
                (output / row["path"]).read_bytes(),
                expected_asset_key=row["asset_key"],
                expected_payload_sha256=row["payload_sha256"],
                expected_payload_encoding=row["payload_encoding"],
                expected_decoded_byte_count=row.get("decoded_byte_count"),
            )
            for layer in cast(list[dict[str, Any]], provenance["layers"]):
                key = str(layer["layer"]["key"])
                if key.startswith("animal-source-chronology-"):
                    layer_keys.add(key)
        if row["domain"] != "nodes" or not str(row.get("layer_key", "")).startswith(
            "animal-source-chronology-"
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
    assert layer_keys == set(expected)
    assert observed == {key: value for key, value in expected.items() if value}


@pytest.mark.parametrize(
    "method",
    [
        "animal_sample_chronology_context_available",
        "build_animal_sample_chronology_context",
    ],
)
def test_atlas_refuses_chronology_owner_bypass_and_preserves_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    from bijux_pollenomics.adna.species.homo_sapiens import (
        build_homo_sapiens_runtime_manifest_for_version_dir,
    )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        capture_aadr_map_snapshot,
    )
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.service import generate_multi_country_map
    from tests.support.aadr import write_anno_file

    root = tmp_path / "context"
    root.mkdir()
    held = captured_inputs.capture_animal_chronology_inputs(root, None)
    anno = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        anno, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(anno.parent.parent)
    aadr = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": sha256(anno.read_bytes()).hexdigest()}
    )
    monkeypatch.setattr(atlas_bundle, method, lambda *_args, **_kwargs: False)
    output = tmp_path / "map"
    output.mkdir()
    (output / "prior.txt").write_bytes(b"preserve")
    with pytest.raises(ValueError, match="maintained chronology owner"):
        generate_multi_country_map(
            anno.parent.parent,
            ("Sweden",),
            output,
            "Nordic",
            "nordic",
            context_root=root,
            lake_inputs=SwedenLakeInputs(),
            aadr_map_snapshot=aadr,
            animal_chronology_inputs=held,
        )
    assert (output / "prior.txt").read_bytes() == b"preserve"


def test_chronology_owner_refuses_subclassed_capture(tmp_path: Path) -> None:
    class UntrustedCapture(captured_inputs.AnimalChronologyInputs):
        pass

    forged = UntrustedCapture(tmp_path, None, None)
    with pytest.raises(ValueError, match="bound context"):
        owner.animal_sample_chronology_context_available(
            tmp_path, chronology_inputs=forged
        )
    with pytest.raises(ValueError, match="bound context"):
        repository.load_animal_sample_chronology_corpus(
            tmp_path, chronology_inputs=forged
        )
