"""Explicit Sweden lake inputs cannot drift with Atlas output paths."""

import csv
import hashlib
import io
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import (
    CapturedLakeFile,
    SwedenLakeInputs,
)
from bijux_pollenomics.reporting.bundles.sweden_lake_layers import (
    build_sweden_lake_atlas_layers,
)

from ..fixtures.lake_evidence import lake_scenario_row


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def test_explicit_sources_are_output_location_independent_and_immutable(
    tmp_path: Path,
) -> None:
    row = lake_scenario_row("aggregate", "Aggregate", "1")
    filename = "sweden_lake_evidence_richness_v66_scenarios.csv"
    path = tmp_path / "sources" / filename
    path.parent.mkdir()
    original = csv_bytes([row])
    path.write_bytes(original)
    captured = CapturedLakeFile.read(path, hashlib.sha256(original).hexdigest())
    request = SwedenLakeInputs(scenario=captured)
    path.write_bytes(csv_bytes([dict(row, lake_label="Altered")]))
    first = build_sweden_lake_atlas_layers(
        version="v66",
        staging_output_dir=tmp_path / "first",
        published_output_dir=tmp_path / "other",
        lake_inputs=request,
    )
    second = build_sweden_lake_atlas_layers(
        version="v66",
        staging_output_dir=tmp_path / "second",
        published_output_dir=tmp_path / "elsewhere",
        lake_inputs=request,
    )
    assert first == second
    assert (
        len(first) == 1
        and cast(list[dict[str, Any]], first[0]["features"])[0]["title"] == "Lake Alpha"
    )
    assert (
        cast(dict[str, Any], first[0]["lake_input_sha256"])["scenario"]
        == hashlib.sha256(original).hexdigest()
    )
    with pytest.raises(ValueError, match="digest"):
        CapturedLakeFile.read(path, hashlib.sha256(original).hexdigest())


def test_explicit_absence_disables_accidental_ancestor_layer(tmp_path: Path) -> None:
    row = lake_scenario_row("aggregate", "Aggregate", "1")
    folder = tmp_path / "report/countries/sweden"
    folder.mkdir(parents=True)
    (folder / "sweden_lake_evidence_richness_v66_scenarios.csv").write_bytes(
        csv_bytes([row])
    )
    kwargs: dict[str, Any] = {
        "version": "v66",
        "staging_output_dir": tmp_path / "report/regions/nordic/staging",
        "published_output_dir": tmp_path / "report/regions/nordic",
    }
    assert len(build_sweden_lake_atlas_layers(**kwargs)) == 1
    assert (
        build_sweden_lake_atlas_layers(**kwargs, lake_inputs=SwedenLakeInputs()) == []
    )


def test_explicit_registry_overrides_consensus_and_requires_scenario(
    tmp_path: Path,
) -> None:
    scenario = lake_scenario_row("consensus", "Consensus", "1")
    registry = dict(scenario, lake_label="Registry Lake", scenario_mean_rank="1")
    scenario_bytes = csv_bytes([scenario])
    registry_bytes = csv_bytes([registry])
    a = CapturedLakeFile(
        "sweden_lake_evidence_richness_v66_scenarios.csv",
        scenario_bytes,
        hashlib.sha256(scenario_bytes).hexdigest(),
    )
    b = CapturedLakeFile(
        "sweden_lake_evidence_richness_v66_registry.csv",
        registry_bytes,
        hashlib.sha256(registry_bytes).hexdigest(),
    )
    result = build_sweden_lake_atlas_layers(
        version="v66",
        staging_output_dir=tmp_path / "stage",
        published_output_dir=tmp_path / "out",
        lake_inputs=SwedenLakeInputs(scenario=a, registry=b),
    )
    assert (
        cast(list[dict[str, Any]], result[0]["features"])[0]["title"] == "Registry Lake"
    )
    with pytest.raises(ValueError, match="scenario"):
        SwedenLakeInputs(registry=b)


def test_explicit_empty_input_identity_reaches_public_map_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service

    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(service, "build_context_layers", lambda **_: ([], [], []))
    output = tmp_path / "map"
    service.generate_multi_country_map(
        tmp_path / "v66",
        ("Sweden",),
        output,
        "Map",
        "nordic",
        lake_inputs=SwedenLakeInputs(),
    )
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["sweden_lake_inputs"]["scenario"] is None
    assert (
        contract["sweden_lake_inputs"]["posture"]
        == "caller_captured_not_source_admission"
    )


def test_empty_registry_is_distinct_from_absent_registry(tmp_path: Path) -> None:
    scenario = lake_scenario_row("consensus", "Consensus", "1")
    content = csv_bytes([scenario])
    registry_header = content.splitlines(keepends=True)[0]
    scenario_file = CapturedLakeFile(
        "sweden_lake_evidence_richness_v66_scenarios.csv",
        content,
        hashlib.sha256(content).hexdigest(),
    )
    empty_registry = CapturedLakeFile(
        "sweden_lake_evidence_richness_v66_registry.csv",
        registry_header,
        hashlib.sha256(registry_header).hexdigest(),
    )
    common: dict[str, Any] = {
        "version": "v66",
        "staging_output_dir": tmp_path / "stage",
        "published_output_dir": tmp_path / "output",
    }
    absent = SwedenLakeInputs(scenario=scenario_file)
    present = SwedenLakeInputs(scenario=scenario_file, registry=empty_registry)
    assert len(build_sweden_lake_atlas_layers(**common, lake_inputs=absent)) == 1
    assert build_sweden_lake_atlas_layers(**common, lake_inputs=present) == []
    assert absent.identity()["registry"] is None
    assert present.identity()["registry"] == hashlib.sha256(registry_header).hexdigest()


def test_captured_input_rejects_symlink_and_release_mismatch(tmp_path: Path) -> None:
    directory = tmp_path / "real"
    directory.mkdir()
    file = directory / "sweden_lake_evidence_richness_v66_scenarios.csv"
    content = csv_bytes([lake_scenario_row("aggregate", "Aggregate", "1")])
    file.write_bytes(content)
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError):
        CapturedLakeFile.read(alias / file.name, hashlib.sha256(content).hexdigest())
    captured = CapturedLakeFile.read(file, hashlib.sha256(content).hexdigest())
    with pytest.raises(ValueError, match="release"):
        build_sweden_lake_atlas_layers(
            version="v67",
            staging_output_dir=tmp_path / "stage",
            published_output_dir=tmp_path / "out",
            lake_inputs=SwedenLakeInputs(scenario=captured),
        )
    with pytest.raises(ValueError, match="name"):
        CapturedLakeFile("../unsafe.csv", content, hashlib.sha256(content).hexdigest())


def test_explicit_nonempty_source_reaches_map_and_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service

    row = lake_scenario_row("consensus", "Consensus", "1")
    registry_row = dict(row, lake_label="Registry Lake", scenario_mean_rank="1")
    content = csv_bytes([row])
    registry_content = csv_bytes([registry_row])
    digest = hashlib.sha256(content).hexdigest()
    registry_digest = hashlib.sha256(registry_content).hexdigest()
    source_dir = tmp_path / "captured"
    source_dir.mkdir()
    scenario_path = source_dir / "sweden_lake_evidence_richness_v66_scenarios.csv"
    registry_path = source_dir / "sweden_lake_evidence_richness_v66_registry.csv"
    scenario_path.write_bytes(content)
    registry_path.write_bytes(registry_content)
    captured = CapturedLakeFile.read(scenario_path, digest)
    captured_registry = CapturedLakeFile.read(registry_path, registry_digest)
    scenario_path.write_bytes(csv_bytes([dict(row, lake_label="Altered Scenario")]))
    registry_path.write_bytes(
        csv_bytes([dict(registry_row, lake_label="Altered Registry")])
    )
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(service, "build_context_layers", lambda **_: ([], [], []))
    output = tmp_path / "map"
    service.generate_multi_country_map(
        tmp_path / "v66",
        ("Sweden",),
        output,
        "Map",
        "nordic",
        lake_inputs=SwedenLakeInputs(scenario=captured, registry=captured_registry),
    )
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["sweden_lake_inputs"]["scenario"] == digest
    assert contract["sweden_lake_inputs"]["registry"] == registry_digest
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    manifest = json.loads((output / "nordic_map_assets.json").read_bytes())
    inventory = normalize_asset_inventory(manifest["assets"])

    def decode(row: dict[str, Any]) -> dict[str, Any]:
        content = (output / row["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == row["sha256"]
        return decode_chunk_script(
            content,
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row.get("decoded_byte_count"),
        )

    provenance = decode(next(row for row in inventory if row["domain"] == "provenance"))
    selected = [
        entry["layer"]
        for entry in provenance["layers"]
        if entry["layer"]["key"] == "sweden-lake-consensus-top40"
    ]
    assert len(selected) == 1
    assert selected[0]["lake_input_sha256"] == {
        "scenario": digest,
        "registry": registry_digest,
        "traceability": None,
    }
    nodes = [
        feature
        for row in inventory
        if row["domain"] == "nodes"
        and row.get("layer_key") == "sweden-lake-consensus-top40"
        for feature in decode(row)["features"]
    ]
    assert [row["title"] for row in nodes] == ["Registry Lake"]


def test_request_refuses_uncaptured_input_objects() -> None:
    with pytest.raises(ValueError, match="captured"):
        SwedenLakeInputs(scenario=object())  # type: ignore[arg-type]
