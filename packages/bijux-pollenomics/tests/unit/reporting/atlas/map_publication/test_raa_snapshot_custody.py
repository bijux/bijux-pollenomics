"""Actual context, contract, node and download paths share one captured epoch."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest
from bijux_pollenomics.reporting.context import artifacts, raa
from bijux_pollenomics.reporting.context.polygons import (
    build_country_boundary_layer,
    build_density_polygon_layer,
    build_external_polygon_layer,
)
from bijux_pollenomics.reporting.context.raa_staging import stage_raa_publication
from bijux_pollenomics.reporting.map_document.static_assets.nodes import (
    build_node_payloads,
)
from bijux_pollenomics.reporting.map_publication import _serialize_layer_contract_row
from bijux_pollenomics.reporting.scope_policy import resolve_map_scope_policy

from tests.support.context_data.raa import (
    REVIEW_INPUT_PATHS,
    geometry,
    inventory,
    read_json,
    write_authority_fixture,
    write_json,
)


def _stage(
    root: Path, output: Path
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    output.mkdir(exist_ok=True)
    return artifacts.stage_context_polygon_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=output,
        build_country_boundary_layer_fn=build_country_boundary_layer,
        build_density_polygon_layer_fn=build_density_polygon_layer,
        build_external_polygon_layer_fn=build_external_polygon_layer,
    )


def test_publication_uses_modern_included_numerator_and_bound_review(
    tmp_path: Path,
) -> None:
    root = tmp_path / "inputs"
    write_authority_fixture(
        root,
        source=inventory(
            ["Fornlämning", " fornlämning ", "FORNLÄMNING", " Fornlämning "]
        ),
    )
    status = raa.build_raa_atlas_input_status(root)
    assert status["atlas_input_status"] == "admitted"
    accounting = cast(dict[str, Any], status["density_count_accounting"])
    assert accounting["metadata_fornlamning_count"] == 4
    assert (
        accounting["density_cell_count_sum"]
        == accounting["expected_included_count"]
        == 2
    )
    assert accounting["reconciled"]
    layers, _ = _stage(root, tmp_path / "bundle")
    row = _serialize_layer_contract_row(
        layers[0], policy=resolve_map_scope_policy(None)
    )
    assert (
        cast(dict[str, Any], row["density_count_accounting"])["expected_included_count"]
        == 2
    )
    review_path = root / "raa/review/spatiotemporal_review.json"
    review = read_json(review_path)
    del review["schema_version"]
    write_json(review_path, review)
    assert (
        cast(dict[str, Any], raa.build_raa_atlas_input_status(root)["review"])[
            "accepted"
        ]
        is False
    )


@pytest.mark.parametrize("timing", ["control", "after_capture", "before_publication"])
def test_source_mutation_cannot_replace_snapshot_status_geometry_or_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timing: str
) -> None:
    from bijux_pollenomics.reporting.context import raa_staging

    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    path = root / REVIEW_INPUT_PATHS["normalized_density"]
    original = path.read_bytes()
    original_geojson = read_json(path)
    changed = deepcopy(original_geojson)
    changed["features"][0]["geometry"] = geometry(19, 58, 20, 59)
    events: list[str] = []
    from bijux_pollenomics.collection.sources.raa.authority import (
        capture_raa_authority_snapshot,
    )

    real_capture = capture_raa_authority_snapshot
    real_publish = raa_staging.stage_raa_publication

    def capture_then_change(context: Path) -> Any:
        snapshot = real_capture(context)
        assert snapshot.decision.admitted
        if timing == "after_capture":
            events.append(timing)
            write_json(path, changed)
        return snapshot

    def publication_then_change(*args: Any, **kwargs: Any) -> Any:
        if timing == "before_publication":
            events.append(timing)
            write_json(path, changed)
        return real_publish(*args, **kwargs)

    monkeypatch.setattr(raa, "capture_raa_authority_snapshot", capture_then_change)
    monkeypatch.setattr(artifacts, "stage_raa_publication", publication_then_change)
    layers, extras = _stage(root, output)
    assert events == ([] if timing == "control" else [timing])
    assert len(layers) == 1
    layer = layers[0]
    row = _serialize_layer_contract_row(layer, policy=resolve_map_scope_policy(None))
    _, nodes = build_node_payloads(
        slug="synthetic-custody",
        version="synthetic",
        point_layers=[],
        polygon_layers=layers,
    )
    assert row["authority_status"] == "admitted"
    assert (
        cast(list[dict[str, Any]], nodes[0]["features"])[0]["geometry"]
        == original_geojson["features"][0]["geometry"]
    )
    publication = output / "context/raa"
    status = read_json(publication / raa.RAA_ATLAS_INPUT_STATUS_FILENAME)
    assert (
        status["inputs"]["normalized_density"]["sha256"] == sha256(original).hexdigest()
    )
    assert (publication / path.name).read_bytes() == original
    assert all((output / relative).is_file() for _, relative in extras)
    assert layer["propagation_status"] == "refused"
    assert layer["scientific_selection_enabled"] is False


def test_destination_only_mutation_refuses_even_when_source_is_still_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    changed = read_json(root / REVIEW_INPUT_PATHS["normalized_density"])
    changed["features"][0]["geometry"] = geometry(19, 58, 20, 59)
    real_write = OwnedTreeWriter.write_bytes
    events: list[str] = []

    def write_then_substitute(
        writer: OwnedTreeWriter, relative: str, content: bytes
    ) -> None:
        real_write(writer, relative, content)
        if relative == "sweden_archaeology_density.geojson":
            events.append(relative)
            write_json(writer.root / relative, changed)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write_then_substitute)
    with pytest.raises(ValueError):
        _stage(root, output)
    assert events == ["sweden_archaeology_density.geojson"]
    assert assess_raa_density_authority(root).admitted
    assert not (output / "context/raa/sweden_archaeology_density.geojson").exists()


def test_foreign_publication_namespace_is_preserved(tmp_path: Path) -> None:
    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    target = output / "context/raa"
    target.mkdir(parents=True)
    foreign = target / "foreign.txt"
    foreign.write_text("preserve foreign work")
    with pytest.raises(ValueError):
        _stage(root, output)
    assert foreign.read_text() == "preserve foreign work"


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_included_count", True),
        ("expected_included_count", -1),
        ("expected_included_count", 1.0),
        ("expected_included_count", "1"),
        ("expected_included_count", 0),
        ("density_cell_count_sum", True),
        ("density_cell_count_sum", 2),
        ("metadata_fornlamning_count", False),
        ("metadata_fornlamning_count", 0),
        ("difference", False),
        ("difference", 1),
        ("reconciled", 1),
        ("reconciled", False),
        ("density_feature_count", True),
        ("density_feature_count", 2),
        ("status", "unsupported"),
        ("foreign", "invented"),
    ],
)
def test_modern_contract_rejects_forged_shapes_types_and_arithmetic(
    tmp_path: Path, field: str, value: object
) -> None:
    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    layers, _ = _stage(root, output)
    layer = deepcopy(layers[0])
    accounting = cast(dict[str, object], layer["density_count_accounting"])
    accounting[field] = value
    with pytest.raises(ValueError):
        _serialize_layer_contract_row(layer, policy=resolve_map_scope_policy(None))


@pytest.mark.parametrize(
    "mutation", ["missing_included", "degraded_modern", "bool_cell", "negative_cell"]
)
def test_modern_contract_refuses_missing_proof_or_contradictory_geometry(
    tmp_path: Path, mutation: str
) -> None:
    root = tmp_path / "inputs"
    write_authority_fixture(root)
    layers, _ = _stage(root, tmp_path / "bundle")
    layer = deepcopy(layers[0])
    if mutation == "missing_included":
        cast(dict[str, object], layer["density_count_accounting"]).pop(
            "expected_included_count"
        )
    elif mutation == "degraded_modern":
        layer.update(
            authority_status="degraded",
            source_authority_admitted=False,
            retained_surface_status="retained_historical_context",
        )
    else:
        geojson = cast(dict[str, Any], layer["geojson"])
        geojson["features"][0]["properties"]["count"] = (
            True if mutation == "bool_cell" else -1
        )
    with pytest.raises(ValueError):
        _serialize_layer_contract_row(layer, policy=resolve_map_scope_policy(None))


def test_owned_publication_replacement_revokes_stale_density_links(
    tmp_path: Path,
) -> None:
    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    original_layers, original_extras = _stage(root, output)
    repeated_layers, repeated_extras = _stage(root, output)
    assert original_layers == repeated_layers
    assert original_extras == repeated_extras
    review_path = root / "raa/review/spatiotemporal_review.json"
    review = read_json(review_path)
    review["release_status"] = "refused"
    write_json(review_path, review)
    layers, extras = _stage(root, output)
    assert not layers
    names = {name for _, name in extras}
    assert names == {
        "context/raa/raa_atlas_input_status.json",
        "context/raa/publication_manifest.json",
    }
    assert not (output / "context/raa/sweden_archaeology_density.geojson").exists()
    assert (
        read_json(output / "context/raa/raa_atlas_input_status.json")["review"][
            "accepted"
        ]
        is False
    )


def test_unknown_prior_manifest_is_preserved(tmp_path: Path) -> None:
    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    _stage(root, output)
    path = output / "context/raa/publication_manifest.json"
    manifest = read_json(path)
    manifest["foreign"] = "preserve unknown prior profile"
    write_json(path, manifest)
    original = path.read_bytes()
    with pytest.raises(ValueError, match="manifest profile"):
        _stage(root, output)
    assert path.read_bytes() == original


def test_output_substitution_during_actual_layer_builder_refuses_before_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, output = tmp_path / "inputs", tmp_path / "bundle"
    write_authority_fixture(root)
    output.mkdir()
    events: list[str] = []
    directories: list[Path] = []
    real_stage = stage_raa_publication

    @contextmanager
    def observe_stage(**kwargs: Any) -> Any:
        with real_stage(**kwargs) as publication:
            directories.append(publication.directory)
            yield publication

    monkeypatch.setattr(artifacts, "stage_raa_publication", observe_stage)

    def build_then_substitute(geojson: dict[str, object]) -> dict[str, object]:
        layer = build_density_polygon_layer(geojson)
        path = directories[0] / "sweden_archaeology_density.geojson"
        assert not path.is_relative_to(output)
        changed = read_json(path)
        changed["features"][0]["geometry"] = geometry(19, 58, 20, 59)
        write_json(path, changed)
        events.append("actual_builder")
        return layer

    with pytest.raises(ValueError):
        artifacts.stage_context_polygon_layers(
            scope_key="nordic",
            context_root=root,
            output_dir=output,
            build_country_boundary_layer_fn=build_country_boundary_layer,
            build_density_polygon_layer_fn=build_then_substitute,
            build_external_polygon_layer_fn=build_external_polygon_layer,
        )
    assert events == ["actual_builder"]


def test_revoked_density_is_absent_from_actual_public_report_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.reporting.bundles.report_partitions.inventory import (
        relative_file_inventory,
    )

    root, output = tmp_path / "inputs", tmp_path / "public-bundle"
    write_authority_fixture(root)
    receipts: list[Path] = []
    real_stage = stage_raa_publication

    @contextmanager
    def observe_stage(**kwargs: Any) -> Any:
        with real_stage(**kwargs) as publication:
            receipts.append(publication.receipt_path)
            yield publication

    monkeypatch.setattr(artifacts, "stage_raa_publication", observe_stage)
    _stage(root, output)
    original = (output / "context/raa/sweden_archaeology_density.geojson").read_bytes()
    review_path = root / "raa/review/spatiotemporal_review.json"
    review = read_json(review_path)
    review["release_status"] = "refused"
    write_json(review_path, review)
    layers, links = _stage(root, output)
    assert layers == []
    assert not any(
        name.endswith("sweden_archaeology_density.geojson") for _, name in links
    )
    inventory_names = relative_file_inventory(output)
    assert not any(
        name.endswith("sweden_archaeology_density.geojson") for name in inventory_names
    )
    receipt = read_json(receipts[-1])
    retained = Path(receipt["recovery"]) / "prior/sweden_archaeology_density.geojson"
    assert not retained.is_relative_to(output)
    assert retained.read_bytes() == original
    assert read_json(receipts[-1].parent / "terminal.json")["status"] == "published"


def test_native_builder_failure_never_attaches_private_candidate(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.bundles.report_partitions.inventory import (
        relative_file_inventory,
    )

    root, output = tmp_path / "inputs", tmp_path / "public-bundle"
    write_authority_fixture(root)
    output.mkdir()
    failure = RuntimeError("synthetic native layer failure")

    def fail_layer(geojson: dict[str, object]) -> dict[str, object]:
        assert geojson["type"] == "FeatureCollection"
        raise failure

    with pytest.raises(RuntimeError) as observed:
        artifacts.stage_context_polygon_layers(
            scope_key="nordic",
            context_root=root,
            output_dir=output,
            build_country_boundary_layer_fn=build_country_boundary_layer,
            build_density_polygon_layer_fn=fail_layer,
            build_external_polygon_layer_fn=build_external_polygon_layer,
        )
    assert observed.value is failure
    assert relative_file_inventory(output) == ()
    note = next(
        note
        for note in getattr(failure, "__notes__", [])
        if "retained operation receipt" in note
    )
    receipt = read_json(Path(note.split("retained operation receipt: ", 1)[1]))
    retained = Path(receipt["candidate"]) / "sweden_archaeology_density.geojson"
    assert not retained.is_relative_to(output)
    assert (
        retained.read_bytes()
        == (root / REVIEW_INPUT_PATHS["normalized_density"]).read_bytes()
    )


def test_terminal_receipt_failure_rolls_candidate_out_of_public_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter
    from bijux_pollenomics.reporting.bundles.report_partitions.inventory import (
        relative_file_inventory,
    )

    root, output = tmp_path / "inputs", tmp_path / "public-bundle"
    write_authority_fixture(root)
    failure = OSError("synthetic private terminal receipt failure")
    real_write = OwnedTreeWriter.write_bytes

    def refuse_terminal(writer: OwnedTreeWriter, relative: str, raw: bytes) -> None:
        if relative == "terminal.json":
            raise failure
        real_write(writer, relative, raw)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", refuse_terminal)
    with pytest.raises(OSError) as observed:
        _stage(root, output)
    assert observed.value is failure
    assert relative_file_inventory(output) == ()
    note = next(
        note
        for note in getattr(failure, "__notes__", [])
        if "retained operation receipt" in note
    )
    receipt = read_json(Path(note.split("retained operation receipt: ", 1)[1]))
    retained = (
        Path(receipt["recovery"])
        / "refused-publication/sweden_archaeology_density.geojson"
    )
    assert not retained.is_relative_to(output)
    assert (
        retained.read_bytes()
        == (root / REVIEW_INPUT_PATHS["normalized_density"]).read_bytes()
    )
