"""Native capture admission, exact retained projections and output confinement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    atlas_source_views as capture,
)
from bijux_pollenomics_dev.source_completion.atlas_browser import (
    capture_projection as publication,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, Any]]:
    """Use controlled receipt fixtures; these are not actual browser evidence."""
    root = tmp_path / "repository"
    directory = root / Path(capture.CAPTURE_PATH).parent
    directory.mkdir(parents=True)
    (root / "artifacts").mkdir()
    (root / "source.txt").write_text("controlled source\n", encoding="utf-8")
    members = []

    def retain(name: str, raw: object) -> str:
        path = directory / name
        _write(path, raw)
        members.append(
            {"path": name, "sha256": _sha(path), "bytes": path.stat().st_size}
        )
        return name

    served = retain("served/map.json", {"fixture": True})
    generations = {}
    for name in (
        "context-frames",
        "nordic-source-contexts",
        "modeled-panels",
        "source-details",
    ):
        generations[name] = retain(
            "generations/" + name + ".json",
            {
                "inputs_sha256": {"source.txt": _sha(root / "source.txt")},
                "candidate_build_id": "fixture-candidate",
                "source_atlas_build_id": "fixture-source",
                "countries": ["Sweden"],
                "source_records": [{"record_id": "fixture-source-record"}],
                "numerical_execution": "none; controlled retained source fixture",
                "source_feature_count": 1,
                "source_feature_sha256": "a" * 64,
                "panel_csv_sha256": "b" * 64,
                "panel_rows": 1,
            },
        )
    cases = []
    verifier_sources = {}
    for name in sorted(capture.CASE_IDS):
        verifier = (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/"
            + name
            + ".mjs"
        )
        path = root / verifier
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// controlled native source fixture\n", encoding="utf-8")
        verifier_sources[verifier] = _sha(path)
        receipt = retain(
            "observations/" + name + ".json",
            {
                "status": "PASS",
                "runtime_errors": [],
                "browser": {"product": "Chrome/155.0.8059.40"},
                "verifier_sha256": _sha(path),
                "served_files_sha256": {"map.json": _sha(directory / served)},
                "keyboard_routes": [1, 2],
                "downloads": [],
                "provider_fallbacks": [1],
                "tile_free_modes": [1],
                "layout_negative_controls": {"status_covering_legend_refused": True},
                "scenarios": [
                    {
                        "source_records_equal": True,
                        "estimates_and_standard_errors_equal": True,
                        "panel_csv_equal": True,
                    }
                ],
                "blocked_tile_requests": 0,
            },
        )
        generation = (
            "modeled-panels"
            if name == "modeled-panel-browser"
            else "nordic-source-contexts"
        )
        cases.append(
            {
                "case_id": name,
                "generation": generations[generation],
                "receipt": receipt,
                "source_candidate": capture.SOURCE_CANDIDATE,
                "served_files": {"map.json": served},
                "native_execution": {
                    "native_exit": 0,
                    "timeout": False,
                    "actual_argv": ["node", verifier],
                },
            },
        )
    owner_ids = sorted(capture.OWNER_IDS)
    products = [
        {
            "owner_id": owner_ids[i % len(owner_ids)],
            "output_path": f"atlas/fixture/observation-{i}.json",
            "operation": "copy",
            "source": served,
        }
        for i in range(43)
    ]
    audit = retain(
        "independent-review.json",
        {
            "candidate": capture.SOURCE_CANDIDATE,
            "counts": {
                "successful_probes": 8,
                "served_file_digests_checked": 134,
                "download_or_screenshot_hashes_checked": 88,
                "source_table_full_equalities": 90,
                "live_DOM_negative_refusals": 4,
                "visually_inspected_PNGs": 8,
            },
        },
    )
    captured_source = directory / "source/source.txt"
    captured_source.parent.mkdir(parents=True)
    captured_source.write_bytes((root / "source.txt").read_bytes())
    members.append(
        {
            "path": "source/source.txt",
            "sha256": _sha(captured_source),
            "bytes": captured_source.stat().st_size,
        }
    )
    document = {
        "schema_version": "atlas-source-view-native-capture.v1",
        "source_candidate": capture.SOURCE_CANDIDATE,
        "scientific_admission": False,
        "numerical_execution": False,
        "browser": "Chrome/155.0.8059.40",
        "files": members,
        "source_footprint": {"source.txt": _sha(root / "source.txt")},
        "source_members": {"source.txt": "source/source.txt"},
        "verifier_sources": verifier_sources,
        "generations": generations,
        "generator_executions": [
            {"id": name, "native_exit": 0, "timeout": False}
            for name in (
                "generate-source-details",
                "generate-Nordic-source-contexts",
                "generate-modeled-panels",
                "generate-context-frames",
            )
        ],
        "independent_review": {"member": audit},
        "cases": cases,
        "products": products,
        "preceding_failures": {
            "original_aggregate_native_exit": 1,
            "successful_original_observations": 6,
            "successful_successor_observations": 2,
        },
        "limits": ["Controlled fixture, not browser execution or scientific evidence"],
    }
    manifest = root / capture.CAPTURE_PATH
    _write(manifest, document)
    monkeypatch.setattr(capture, "CAPTURE_SHA256", _sha(manifest))
    monkeypatch.setattr(publication, "CAPTURE_SHA256", _sha(manifest))
    selector = root / publication.SELECTOR_ROOT / "selection.json"
    _write(
        selector,
        {
            "schema_version": publication.SELECTOR_SCHEMA,
            "owner_id": owner_ids[0],
            "capture_sha256": _sha(manifest),
        },
    )
    return root, selector, document


def _reseal(
    root: Path, document: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = root / capture.CAPTURE_PATH
    _write(manifest, document)
    monkeypatch.setattr(capture, "CAPTURE_SHA256", _sha(manifest))
    monkeypatch.setattr(publication, "CAPTURE_SHA256", _sha(manifest))


def test_all_twelve_owner_projections_preserve_raw_bytes(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, selector, document = packet
    union: dict[str, bytes] = {}
    for owner in sorted(capture.OWNER_IDS):
        _write(
            selector,
            {
                "schema_version": publication.SELECTOR_SCHEMA,
                "owner_id": owner,
                "capture_sha256": capture.CAPTURE_SHA256,
            },
        )
        products = publication.build_capture_products(root, selector)
        expected = {
            row["output_path"]
            for row in document["products"]
            if row["owner_id"] == owner
        }
        assert set(products) == expected
        assert not set(union).intersection(products)
        union.update(products)
    assert len(union) == 43
    assert all(value == next(iter(union.values())) for value in union.values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("scientific_admission", True),
        ("source_candidate", "a" * 40),
        ("browser", "OtherBrowser"),
    ],
)
def test_changed_capture_authority_is_refused(
    packet: tuple[Path, Path, dict[str, Any]],
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, document = packet
    document[field] = value
    _reseal(root, document, monkeypatch)
    with pytest.raises(ReportRebuildError, match="identity or admission"):
        capture.validated_atlas_source_views(root)


@pytest.mark.parametrize(
    "kind", ["certificate", "raw", "source", "verifier", "missing", "extra", "symlink"]
)
def test_changed_physical_capture_or_source_is_refused(
    packet: tuple[Path, Path, dict[str, Any]], kind: str
) -> None:
    root, _, document = packet
    directory = (root / capture.CAPTURE_PATH).parent
    target = directory / "served/map.json"
    if kind == "certificate":
        (root / capture.CAPTURE_PATH).write_text("{}\n", encoding="utf-8")
    elif kind == "raw":
        target.write_text("changed", encoding="utf-8")
    elif kind == "source":
        (root / "source.txt").write_text("changed", encoding="utf-8")
    elif kind == "verifier":
        (root / next(iter(document["verifier_sources"]))).write_text(
            "changed", encoding="utf-8"
        )
    elif kind == "missing":
        target.unlink()
    elif kind == "extra":
        (directory / "unexpected.json").write_text("{}", encoding="utf-8")
    else:
        target.unlink()
        target.symlink_to(root / "source.txt")
    with pytest.raises((ReportRebuildError, ValueError)):
        capture.validated_atlas_source_views(root)


@pytest.mark.parametrize(
    "change",
    [
        "native_failure",
        "native_timeout",
        "missing_case",
        "served_mismatch",
        "unknown_owner",
        "duplicate_product",
        "escaping_member",
    ],
)
def test_incomplete_native_or_owner_lineage_is_refused(
    packet: tuple[Path, Path, dict[str, Any]],
    change: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, document = packet
    if change == "native_failure":
        document["cases"][0]["native_execution"]["native_exit"] = 1
    elif change == "native_timeout":
        document["cases"][0]["native_execution"]["timeout"] = True
    elif change == "missing_case":
        document["cases"].pop()
    elif change == "served_mismatch":
        document["cases"][0]["served_files"] = {}
    elif change == "unknown_owner":
        document["products"][0]["owner_id"] = "atlas/unreviewed/owner"
    elif change == "duplicate_product":
        document["products"][1]["output_path"] = document["products"][0]["output_path"]
    else:
        document["files"][0]["path"] = "../escaped.json"
    _reseal(root, document, monkeypatch)
    with pytest.raises((ReportRebuildError, ValueError)):
        capture.validated_atlas_source_views(root)


@pytest.mark.parametrize(
    "operation,owner",
    [
        ("keyless-identity", "atlas/keyless-cache-matrix/candidate-identity"),
        ("provider-review", "atlas/provider-accessibility/browser-evidence"),
        ("modeled-review", "atlas/modeled-panel-browser/browser-evidence"),
    ],
)
def test_metadata_projection_uses_actual_capture_not_historical_summaries(
    packet: tuple[Path, Path, dict[str, Any]],
    operation: str,
    owner: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, selector, document = packet
    selected = next(row for row in document["products"] if row["owner_id"] == owner)
    selected["operation"] = operation
    _reseal(root, document, monkeypatch)
    _write(
        selector,
        {
            "schema_version": publication.SELECTOR_SCHEMA,
            "owner_id": owner,
            "capture_sha256": capture.CAPTURE_SHA256,
        },
    )
    value = json.loads(
        publication.build_capture_products(root, selector)[selected["output_path"]]
    )
    assert value["source_capture"]["browser_executed_by_this_projection"] is False
    assert value["source_capture"]["scientific_admission"] is False
    if operation == "keyless-identity":
        assert value["source_record_ids"] == ["fixture-source-record"]
    elif operation == "provider-review":
        assert value["selected_checks"]["keyboard_routes"] == 2
        assert value["selected_checks"]["layout_negative_controls"][
            "status_covering_legend_refused"
        ]
    else:
        assert value["frozen_source_input_count"] == 1
        assert value["scenario_count"] == 1
        assert value["panel_csv_equal"] is True


@pytest.mark.parametrize("mode", ["outside", "parent", "symlink", "existing"])
def test_writer_rejects_invalid_destination_before_creating_files(
    packet: tuple[Path, Path, dict[str, Any]], mode: str, tmp_path: Path
) -> None:
    root, selector, _ = packet
    output = root / "artifacts/output"
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "parent":
        output = root / "artifacts" / ".." / "escaped"
    elif mode == "symlink":
        (root / "artifacts/link").symlink_to(tmp_path, target_is_directory=True)
        output = root / "artifacts/link/output"
    else:
        output.mkdir()
    with pytest.raises((ReportRebuildError, ValueError)):
        publication.publish_capture_products(root, selector, output)
    assert not (root / "escaped").exists()
    assert not (tmp_path / "outside").exists()


def test_additive_api_witness_keeps_every_original_function_node() -> None:
    original = b"def existing():\n    return 1\n\n__all__ = ['existing']\n"
    added = b"from engine.addition import Added\n\ndef existing():\n    return 1\n\n__all__ = ['Added', 'existing']\n"
    proof = {
        "additional_imports": {"engine.addition": ["Added"]},
        "additional_exports": ["Added"],
        "additional_capabilities": [],
    }
    import ast

    assert capture._api_without_adoptions(added, proof) == ast.dump(
        ast.parse(original), include_attributes=False
    )
    assert capture._api_without_adoptions(
        added.replace(b"return 1", b"return 2"), proof
    ) != ast.dump(ast.parse(original), include_attributes=False)


def test_changed_adopted_api_without_exact_certificate_is_refused(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, _ = packet
    with pytest.raises((ReportRebuildError, ValueError)):
        capture._validate_api_adoption(root, root / "source.txt", root / "source.txt")
