"""Later provider citations bind exact dataset/site relations and cache content."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting import service as reports
from bijux_pollenomics.reporting.bundles import atlas_bundle
from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    build_map_evidence_projection,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma_publications as citations,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)

from .test_source_site_links import source as source


def publication(
    dataset: int, site: int, identity: int, primary: bool | None
) -> dict[str, Any]:
    return {
        "publication": {
            "publicationid": identity,
            "datasets": [{"datasetid": dataset, "siteid": site, "primary": primary}],
            "citation": "Original <literal> citation",
            "articletitle": "Native title",
            "author": [{"familyname": "Native", "givennames": "Author", "order": 1}],
            "year": "1994",
            "journal": None,
            "pages": "1–82",
            "doi": None,
            "pubtype": "Doctoral Dissertation",
            "url": "javascript:untrusted()",
        }
    }


def save_capture(
    root: Path,
    responses: dict[int, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    root.mkdir(exist_ok=True)
    (root / "responses").mkdir(exist_ok=True)
    records = []
    for dataset, data in responses.items():
        payload = json.dumps({"status": "success", "data": data}).encode()
        relative = f"responses/dataset-{dataset}-publications.json"
        (root / relative).write_bytes(payload)
        records.append(
            {
                "dataset_id": dataset,
                "path": relative,
                "http_status": 200,
                "url": f"{citations.PUBLICATION_SOURCE_API}{dataset}/publications",
                "retrieved_at_utc": "2026-09-29T02:41:47.238255+00:00",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "publication_count": len(data),
            }
        )
    payload = json.dumps(
        {
            "schema_version": "neotoma-candidate-publication-capture.v1",
            "source_api": citations.PUBLICATION_SOURCE_API,
            "response_count": len(records),
            "responses": records,
        }
    ).encode()
    (root / "capture-manifest.json").write_bytes(payload)
    monkeypatch.setattr(
        citations,
        "PUBLICATION_CAPTURE_MANIFEST_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )
    return root


@pytest.fixture
def capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return save_capture(
        tmp_path / "citations",
        {
            201: [publication(201, 20, 501, True)],
            2021: [publication(2021, 21, 502, None)],
        },
        monkeypatch,
    )


def decoded(table: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(table["fields"], row, strict=True)) for row in table["records"]]


def projected(
    source: tuple[Path, dict[str, Any], dict[str, Any]], capture: Path | None = None
) -> Any:
    root, layer, _ = source
    return build_map_evidence_projection(
        root, [deepcopy(layer)], publication_capture_root=capture
    )


def test_native_publications_are_separate_from_pollen_epoch_and_site_isolated(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
) -> None:
    before = deepcopy(source[2])
    legacy = projected(source)
    result = projected(source, capture)
    for old, new in zip(legacy.detail_records, result.detail_records, strict=True):
        plain = deepcopy(new)
        context = plain["tabs"]["provenance"].pop("publication_capture")
        assert plain == old
        datasets = decoded(context["datasets"])
        publications = decoded(context["publications"])
        identity = 201 if new["record_id"] == "neotoma:site:20" else 2021
        assert len(datasets) == len(publications) == 1
        assert publications[0]["dataset_id"] == f"neotoma:dataset:{identity}"
        assert (
            publications[0]["source_payload"]
            == publication(
                identity,
                20 if identity == 201 else 21,
                501 if identity == 201 else 502,
                True if identity == 201 else None,
            )["publication"]
        )
        assert datasets[0]["retrieved_at_utc"].startswith("2026-09-29")
        assert (
            context["epoch_posture"]
            == "separate_provider_capture_not_original_pollen_snapshot"
        )
        assert (
            context["manifest_sha256"] == citations.PUBLICATION_CAPTURE_MANIFEST_SHA256
        )
    assert source[2] == before
    assert result.point_layers == legacy.point_layers
    assert result.reconciliation == legacy.reconciliation


@pytest.mark.parametrize(
    "state", ["uncovered", "no_links", "false", "null", "multiple"]
)
def test_uncovered_empty_nullable_and_multiple_primary_populations_are_distinct(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    data = (
        []
        if state == "no_links"
        else [publication(201, 20, 501, False if state == "false" else None)]
    )
    if state == "multiple":
        data = [publication(201, 20, 501, True), publication(201, 20, 502, True)]
    root = save_capture(
        tmp_path / "packet", {} if state == "uncovered" else {201: data}, monkeypatch
    )
    result = projected(source, root)
    capture = result.detail_records[0]["tabs"]["provenance"]["publication_capture"]
    dataset = decoded(capture["datasets"])[0]
    expected = {
        "uncovered": "not_captured",
        "no_links": "no_publication_link",
        "false": "no_source_primary_flag",
        "null": "no_source_primary_flag",
        "multiple": "multiple_source_primary_publications",
    }[state]
    assert dataset["status"] == expected
    assert dataset["publication_count"] == (None if state == "uncovered" else len(data))
    expected_flags = (
        []
        if state == "uncovered"
        else [row["publication"]["datasets"][0]["primary"] for row in data]
    )
    assert [
        row["source_primary_flag"] for row in decoded(capture["publications"])
    ] == expected_flags


@pytest.mark.parametrize(
    "field,value",
    [
        ("datasetid", 999),
        ("datasetid", True),
        ("siteid", 21),
        ("primary", 1),
        ("publicationid", True),
        ("duplicate", True),
    ],
)
def test_wrong_site_or_dataset_malformed_primary_and_duplicate_publications_refuse(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    entry = publication(201, 20, 501, True)
    if field in {"datasetid", "siteid", "primary"}:
        entry["publication"]["datasets"][0][field] = value
    elif field == "publicationid":
        entry["publication"][field] = value
    rows = [entry, deepcopy(entry)] if field == "duplicate" else [entry]
    root = save_capture(tmp_path / "bad", {201: rows}, monkeypatch)
    with pytest.raises(ValueError):
        projected(source, root)


@pytest.mark.parametrize("change", ["manifest", "response", "missing", "symlink"])
def test_configured_capture_tampering_is_never_silently_unavailable(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
    change: str,
) -> None:
    path = capture / "responses/dataset-201-publications.json"
    if change == "manifest":
        (capture / "capture-manifest.json").write_bytes(b"{}")
    elif change == "response":
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "missing":
        path.unlink()
    else:
        target = capture / "saved.json"
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises((ValueError, OSError)):
        projected(source, capture)


def test_only_projected_dataset_responses_are_opened(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads((capture / "capture-manifest.json").read_bytes())
    extra = dict(
        manifest["responses"][0],
        dataset_id=9999,
        path="responses/dataset-9999-publications.json",
    )
    manifest["responses"].append(extra)
    manifest["response_count"] += 1
    payload = json.dumps(manifest).encode()
    (capture / "capture-manifest.json").write_bytes(payload)
    monkeypatch.setattr(
        citations,
        "PUBLICATION_CAPTURE_MANIFEST_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )
    assert len(projected(source, capture).detail_records) == 2
    assert not (capture / extra["path"]).exists()


def test_response_change_during_projection_refuses(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read = citations._read
    selected = capture / "responses/dataset-201-publications.json"
    changed = False

    def change_after_read(path: Path, limit: int) -> bytes:
        nonlocal changed
        payload = read(path, limit)
        if path == selected and not changed:
            changed = True
            path.write_bytes(payload + b" ")
        return payload

    monkeypatch.setattr(citations, "_read", change_after_read)
    with pytest.raises(ValueError, match="changed during projection"):
        projected(source, capture)


def test_changed_citation_changes_static_build_and_lazy_detail_fingerprint(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def build(name: str) -> Any:
        output = tmp_path / name
        output.mkdir()
        return write_static_atlas_assets(
            output,
            slug="citations",
            version="source",
            point_layers=[],
            polygon_layers=[],
            detail_records=projected(source, capture).detail_records,
        )

    first = build("first")
    changed = publication(201, 20, 501, True)
    changed["publication"]["citation"] = "A different literal citation"
    save_capture(
        capture, {201: [changed], 2021: [publication(2021, 21, 502, None)]}, monkeypatch
    )
    second = build("second")
    assert first.manifest["build_id"] != second.manifest["build_id"]
    assert [p.read_bytes() for p in first.asset_paths if "details" in p.name] != [
        p.read_bytes() for p in second.asset_paths if "details" in p.name
    ]


def test_normal_multi_country_consumer_forwards_explicit_capture_to_real_projection(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, layer, _ = source
    monkeypatch.setattr(
        reports, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        reports,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )
    monkeypatch.setattr(
        reports, "build_context_layers", lambda **_: ([deepcopy(layer)], [], [])
    )
    empty = SimpleNamespace(
        direct_coordinate_feature_count=0,
        named_site_geocoded_feature_count=0,
        weaker_geography_feature_count=0,
    )
    monkeypatch.setattr(
        atlas_bundle,
        "build_tracked_animal_atlas_bundle",
        lambda **_: SimpleNamespace(
            point_layers=[], extra_artifacts=[], localities=(), coordinate_review=empty
        ),
    )
    monkeypatch.setattr(
        atlas_bundle, "animal_sample_chronology_context_available", lambda _: False
    )
    monkeypatch.setattr(atlas_bundle, "build_sweden_lake_atlas_layers", lambda **_: [])
    observed = []

    def projection(context_root: Path, point_layers: Any, **kwargs: Any) -> Any:
        observed.append(kwargs["publication_capture_root"])
        result = build_map_evidence_projection(context_root, point_layers, **kwargs)
        assert cast(dict[str, Any], result.detail_records[0]["tabs"])["provenance"][
            "publication_capture"
        ]
        raise RuntimeError("source projection reached")

    monkeypatch.setattr(atlas_bundle, "build_map_evidence_projection", projection)
    with pytest.raises(RuntimeError, match="source projection reached"):
        reports.generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            tmp_path / "atlas",
            "Map",
            "nordic",
            context_root=root,
            publication_capture_root=capture,
        )
    assert observed == [capture]


def test_boolean_native_payload_does_not_equal_integer_dataset_identity() -> None:
    record: dict[str, object] = {
        "record_id": "neotoma:site:20",
        "tabs": {
            "overview": {"source_site_id": "20"},
            "samples": {
                "datasets": {
                    "fields": ["dataset_id", "source_dataset_id", "source_payload"],
                    "record_count": 1,
                    "records": [["neotoma:dataset:1", 1, {"datasetid": True}]],
                }
            },
        },
    }
    with pytest.raises(ValueError, match="positive safe integer"):
        citations._datasets(record)


@pytest.mark.parametrize("prebuilt", [False, True])
def test_capture_cannot_be_ignored_without_source_projection(
    tmp_path: Path,
    prebuilt: bool,
) -> None:
    with pytest.raises(ValueError, match="requires source-projected atlas details"):
        prepare_layers(
            tmp_path,
            report=None,
            version="source",
            all_samples=(),
            context_root=tmp_path if prebuilt else None,
            geography_scope=None,
            build_atlas_bundle_paths_fn=None,
            build_context_layers_fn=None,
            build_samples_geojson_fn=None,
            atlas_detail_records=[] if prebuilt else None,
            atlas_scientific_signals=None,
            atlas_edge_records=None,
            atlas_sequence_records=None,
            surface=None,
            publication_capture_root=tmp_path,
        )
