"""Native capture admission, exact retained projections and output confinement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    generated,
    objects,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    index as retained_index,
)
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


STORAGE_REVISION = "b" * 40
GENERATED_MEMBER = (
    "source/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
_STATES: dict[Path, _GitTransport] = {}


def _oid(raw: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
    ).hexdigest()


class _GitTransport:
    """Substitute only external Git transport; preserve real capsule validation."""

    def __init__(self, root: Path, bodies: dict[str, bytes]) -> None:
        self.root = root
        self.bodies = bodies
        self.fault: str | None = None

    def query(
        self, root: Path, args: list[str], limit: int, deadline: float, executable: Path
    ) -> bytes:
        assert root == self.root
        if args[0] == "cat-file":
            return b"missing\n" if self.fault == "missing_revision" else b"commit\n"
        if args[0] == "merge-base":
            if self.fault == "missing_ancestor":
                raise ValueError("synthetic source ancestor absent")
            return b""
        assert args[:3] == ["ls-tree", "-r", "-z"] and args[3] == STORAGE_REVISION
        rows: list[bytes] = []
        for name in args[5:]:
            if self.fault == "missing_member" and not rows:
                continue
            mode = "120000" if self.fault == "mode" else "100644"
            rows.append(f"{mode} blob {_oid(self.bodies[name])}\t{name}\0".encode())
        if self.fault == "extra_member":
            rows.append(b"100644 blob " + b"0" * 40 + b"\textra.py\0")
        return b"".join(rows)


class _GitPipe:
    def __init__(
        self, root: Path, args: list[str], deadline: float, executable: Path
    ) -> None:
        assert args == ["cat-file", "--batch"]
        self.state = _STATES[root]
        self.stdin = self
        self.header = b""
        self.buffer = b""

    def write(self, request: bytes) -> int:
        revision, path = request.decode().strip().split(":", 1)
        assert revision == STORAGE_REVISION
        raw = self.state.bodies[path]
        self.header = f"{_oid(raw)} blob {len(raw)}".encode()
        if self.state.fault == "body":
            raw = b"x" * len(raw)
        self.buffer = raw + b"\n"
        return len(request)

    def flush(self) -> None:
        pass

    def line(self) -> bytes:
        return self.header

    def exact(self, size: int) -> bytes:
        result, self.buffer = self.buffer[:size], self.buffer[size:]
        return result

    def finish(self) -> None:
        assert not self.buffer

    def close(self) -> None:
        pass


def _refresh_transport(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capture_path: str = capture.CAPTURE_PATH,
) -> None:
    directory = (root / capture_path).parent
    descriptor_path = directory / "source-transport.json"
    descriptor = json.loads(descriptor_path.read_bytes())
    manifest = root / capture_path
    descriptor["capture"] = {
        "name": "capture.json",
        "sha256": _sha(manifest),
        "bytes": manifest.stat().st_size,
    }
    _write(descriptor_path, descriptor)
    index_path = root / retained_index.INDEX_PATH
    index: dict[str, Any] = (
        json.loads(index_path.read_bytes())
        if index_path.exists()
        else {
            "schema_version": "retained-source-index.v1",
            "capsules": {},
            "source_revisions": {},
        }
    )
    index["capsules"][directory.relative_to(root).as_posix()] = {
        "descriptor": "source-transport.json",
        "sha256": _sha(descriptor_path),
        "bytes": descriptor_path.stat().st_size,
    }
    _write(index_path, index)
    monkeypatch.setattr(retained_index, "INDEX_SHA256", _sha(index_path))
    monkeypatch.setattr(retained_index, "INDEX_BYTES", index_path.stat().st_size)


def _install_transport(
    root: Path,
    bodies: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    *,
    capture_path: str = capture.CAPTURE_PATH,
    source_candidate: str = capture.SOURCE_CANDIDATE,
    package_members: int = 393,
) -> None:
    state = _GitTransport(root, bodies)
    _STATES[root] = state
    (root / ".git").mkdir(exist_ok=True)
    (root / ".git/HEAD").write_text("e" * 40 + "\n")
    monkeypatch.setattr(objects, "query", state.query)
    monkeypatch.setattr(objects, "GitPipe", _GitPipe)
    monkeypatch.setattr(
        objects, "git_executable", lambda: Path(sys.executable).resolve()
    )
    groups = []
    for prefix, count in (("configs/", 6), ("packages/", package_members)):
        mapping = sorted(
            [
                [name, _oid(raw)]
                for name, raw in bodies.items()
                if name.startswith(prefix)
            ]
        )
        assert len(mapping) == count
        groups.append(
            {
                "historical_source_commit": source_candidate,
                "source_revision": STORAGE_REVISION,
                "member_count": count,
                "git_entries_sha256": hashlib.sha256(
                    json.dumps(mapping, separators=(",", ":")).encode()
                ).hexdigest(),
                "prefixes": {
                    "member_prefix": "source/" + prefix,
                    "repository_prefix": prefix,
                },
            }
        )
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {},
        "historical_native_epochs": [source_candidate],
        "source_revision_correspondence": [
            {
                "historical_source_commit": source_candidate,
                "source_revision": STORAGE_REVISION,
            }
        ],
        "git_groups": groups,
        "generated_members": [
            {
                "member": GENERATED_MEMBER,
                "generator": {
                    "provider": generated.PROVIDER,
                    "sha256": generated.GENERATOR_SHA256,
                    "bytes": generated.GENERATOR_BYTES,
                },
                "scalars": {
                    "version": "0.1.9.dev1462",
                    "version_tuple": [0, 1, 9, "dev1462"],
                    "short_node": None,
                },
                "original_generator_execution_claimed": False,
                "original_version_derivation_claimed": False,
            }
        ],
        "rewritten_source_epoch_executed": False,
    }
    _write((root / capture_path).parent / "source-transport.json", descriptor)
    _refresh_transport(root, monkeypatch, capture_path)


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
    footprint = {"source.txt": _sha(root / "source.txt")}
    source_members = {"source.txt": "source/source.txt"}
    git_bodies: dict[str, bytes] = {}
    configs = (
        "country-coverage.schema.json",
        "ecological-classification.v1.yaml",
        "map-visual-profile.v1.yaml",
        "phenomenon-event.schema.json",
        "propagation-candidate.schema.json",
        "propagation-model.v1.yaml",
    )
    canonical = ["configs/scientific-contracts/" + name for name in configs]
    canonical += sorted(capture.HISTORICAL_PORTAL_READER_SOURCES)
    canonical += [
        f"packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/fixture_{i:03}.py"
        for i in range(387)
    ]
    for name in canonical:
        raw = ("# own synthetic source " + name + "\n").encode()
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        git_bodies[name] = raw
        member = "source/" + name
        members.append(
            {
                "path": member,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )
        footprint[name] = hashlib.sha256(raw).hexdigest()
        source_members[name] = member
    for i in range(52):
        name = f"docs/report/fixture/source-{i}.json"
        record = {"own_source": i}
        target = root / name
        _write(target, record)
        member = retain("source/" + name, record)
        footprint[name] = _sha(target)
        source_members[name] = member
    generated_body = generated.serialize("0.1.9.dev1462", (0, 1, 9, "dev1462"))
    assert len(generated_body) == 539
    members.append(
        {
            "path": GENERATED_MEMBER,
            "sha256": hashlib.sha256(generated_body).hexdigest(),
            "bytes": 539,
        }
    )
    generated_name = GENERATED_MEMBER.removeprefix("source/")
    footprint[generated_name] = hashlib.sha256(generated_body).hexdigest()
    source_members[generated_name] = GENERATED_MEMBER
    for i in range(563 - len(members)):
        retain(f"products/fixture/member-{i}.json", {"own_product": i})
    assert len(members) == 563 and len(footprint) == 453
    document = {
        "schema_version": "atlas-source-view-native-capture.v1",
        "source_candidate": capture.SOURCE_CANDIDATE,
        "scientific_admission": False,
        "numerical_execution": False,
        "browser": "Chrome/155.0.8059.40",
        "files": members,
        "source_footprint": footprint,
        "source_members": source_members,
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
    _install_transport(root, git_bodies, monkeypatch)
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
    _refresh_transport(root, monkeypatch)


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
        capture._validate_api_adoption(
            root, (root / "source.txt").read_bytes(), root / "source.txt"
        )


@pytest.mark.parametrize(
    "change",
    [
        "valid",
        "existing_body",
        "old_export",
        "alias",
        "missing",
        "duplicate",
        "nonstring",
    ],
)
def test_root_api_adoption_preserves_existing_semantics(change: str) -> None:
    import ast

    original = b"from .api import Existing\ndef original():\n    return 1\n__all__ = ['Existing']\n"
    added = b"from .api import Existing, TwoTaxonCountingInterval, fixed_two_taxon_counting_interval\ndef original():\n    return 1\n__all__ = ['Existing', 'TwoTaxonCountingInterval', 'fixed_two_taxon_counting_interval']\n"
    proof = {
        "additional_import_names": [
            "TwoTaxonCountingInterval",
            "fixed_two_taxon_counting_interval",
        ],
        "additional_exports": [
            "TwoTaxonCountingInterval",
            "fixed_two_taxon_counting_interval",
        ],
    }
    expected = ast.dump(ast.parse(original), include_attributes=False)
    if change == "existing_body":
        added = added.replace(b"return 1", b"return 2")
    elif change == "old_export":
        added = added.replace(b"['Existing',", b"['Changed',")
    elif change == "nonstring":
        added = added.replace(b"['Existing',", b"['Existing', None,")
    elif change == "alias":
        added = added.replace(
            b"Existing, TwoTaxonCountingInterval,",
            b"Existing, TwoTaxonCountingInterval as Changed,",
        )
    elif change == "missing":
        added = added.replace(b"'TwoTaxonCountingInterval', ", b"")
    elif change == "duplicate":
        added = added.replace(
            b"['Existing',", b"['TwoTaxonCountingInterval', 'Existing',"
        )
    if change in {"alias", "missing", "duplicate"}:
        with pytest.raises((ReportRebuildError, ValueError)):
            capture._root_api_without_adoptions(added, proof)
    else:
        stripped = capture._root_api_without_adoptions(added, proof)
        assert (stripped == expected) is (change == "valid")


def test_root_api_changed_source_without_exact_certificate_is_refused(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, _ = packet
    with pytest.raises((ReportRebuildError, ValueError)):
        capture._validate_root_api_adoption(
            root, (root / "source.txt").read_bytes(), root / "source.txt"
        )


def test_scoped_capsule_keeps_exact_source_and_physical_partitions(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, document = packet
    catalogue = {
        row["path"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in document["files"]
    }
    buffer = retained_index.validated_descriptor(
        root, str(Path(capture.CAPTURE_PATH).parent), catalogue
    )
    assert len(buffer.detached) == 400
    assert len(buffer.descriptor.resolve(root)) == 399
    assert len(buffer.read_source(GENERATED_MEMBER)) == 539
    assert len(buffer.descriptor.members) == 563
    physical = [
        path
        for path in (root / capture.CAPTURE_PATH).parent.rglob("*")
        if path.is_file()
    ]
    assert len(physical) == 165
    assert (
        len(
            [
                name
                for name in buffer.descriptor.members
                if name.startswith("source/") and name not in buffer.detached
            ]
        )
        == 53
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing_revision",
        "missing_ancestor",
        "missing_member",
        "extra_member",
        "mode",
        "body",
    ],
)
def test_git_transport_cannot_weaken_source_guards(
    packet: tuple[Path, Path, dict[str, Any]], fault: str
) -> None:
    root, _, _ = packet
    _STATES[root].fault = fault
    with pytest.raises(ReportRebuildError):
        capture.validated_atlas_source_views(root)


@pytest.mark.parametrize(
    "fault",
    [
        "restored_source",
        "hardlink",
        "generated_claim",
        "map_identity",
        "descriptor_tamper",
    ],
)
def test_detached_and_generated_projection_guards(
    packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    root, _, _ = packet
    directory = (root / capture.CAPTURE_PATH).parent
    descriptor_path = directory / "source-transport.json"
    if fault == "restored_source":
        name, raw = next(iter(_STATES[root].bodies.items()))
        target = directory / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    elif fault == "hardlink":
        (root / "alias").hardlink_to(directory / "served/map.json")
    elif fault == "descriptor_tamper":
        descriptor_path.write_bytes(descriptor_path.read_bytes() + b" ")
    else:
        descriptor = json.loads(descriptor_path.read_bytes())
        if fault == "generated_claim":
            descriptor["generated_members"][0][
                "original_generator_execution_claimed"
            ] = True
        else:
            descriptor["git_groups"][0]["git_entries_sha256"] = "0" * 64
        _write(descriptor_path, descriptor)
        _refresh_transport(root, monkeypatch)
    with pytest.raises(ReportRebuildError):
        capture.validated_atlas_source_views(root)


def test_closed_source_buffer_rejects_changed_epoch_context(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, document = packet
    catalogue = {
        row["path"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in document["files"]
    }
    buffer = retained_index.validated_descriptor(
        root, str(Path(capture.CAPTURE_PATH).parent), catalogue
    )
    (root / ".git/HEAD").write_text("f" * 40 + "\n")
    with pytest.raises(ReportRebuildError, match="context changed"):
        buffer.fresh()


def test_historical_portal_readers_do_not_claim_current_source_reproduction(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, document = packet
    old_packet = (root / capture.CAPTURE_PATH).read_bytes()
    for relative in capture.HISTORICAL_PORTAL_READER_SOURCES:
        (root / relative).write_bytes(b"# Own changed maintained portal reader\n")
    checked = capture.validated_atlas_source_views(root)
    assert checked.document == document
    assert (root / capture.CAPTURE_PATH).read_bytes() == old_packet
    assert checked.document["source_candidate"] == capture.SOURCE_CANDIDATE
    assert checked.document["scientific_admission"] is False
    assert checked.document["numerical_execution"] is False


@pytest.mark.parametrize("defect", ["missing", "symlink", "hardlink"])
def test_current_historical_reader_paths_remain_regular_and_owned(
    packet: tuple[Path, Path, dict[str, Any]], defect: str
) -> None:
    root, _, _ = packet
    target = root / sorted(capture.HISTORICAL_PORTAL_READER_SOURCES)[0]
    body = target.read_bytes()
    target.unlink()
    if defect == "symlink":
        target.symlink_to(root / "source.txt")
    elif defect == "hardlink":
        reference = root / "own-reference.py"
        reference.write_bytes(body)
        target.hardlink_to(reference)
    with pytest.raises((ReportRebuildError, ValueError)):
        capture.validated_atlas_source_views(root)


def test_other_source_paths_cannot_borrow_the_historical_reader_role(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, _ = packet
    relative = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/fixture_000.py"
    (root / relative).write_bytes(b"# Unapproved current source drift\n")
    with pytest.raises(ReportRebuildError, match="source footprint differs"):
        capture.validated_atlas_source_views(root)


def test_historical_reader_git_bodies_remain_authenticated(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, _ = packet
    relative = sorted(capture.HISTORICAL_PORTAL_READER_SOURCES)[0]
    _STATES[root].bodies[relative] = b"# Tampered historical witness\n"
    with pytest.raises((ReportRebuildError, ValueError)):
        capture.validated_atlas_source_views(root)


@pytest.fixture
def sample_chronology_packet(
    packet: tuple[Path, Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, Any]]:
    """Create controlled current-profile receipts without claiming native execution."""
    import copy
    import shutil

    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, selector, historical = packet
    directory = root / Path(current.CURRENT_CAPTURE_PATH).parent
    shutil.copytree(root / Path(capture.CAPTURE_PATH).parent, directory)
    document = copy.deepcopy(historical)
    document.update(
        schema_version="atlas-sample-chronology-source-capture.v2",
        source_candidate=current.CURRENT_SOURCE_CANDIDATE,
        sample_chronology_admission=False,
        source_context={"not_a_clean_git_tree": True},
    )

    def retain(name: str, value: object) -> str:
        path = directory / name
        _write(path, value)
        document["files"] = [row for row in document["files"] if row["path"] != name]
        document["files"].append(
            {"path": name, "sha256": _sha(path), "bytes": path.stat().st_size}
        )
        return name

    generation = retain(
        "generations/sample-chronology.json",
        {"inputs_sha256": {"source.txt": _sha(root / "source.txt")}},
    )
    document["generations"]["sample-chronology"] = generation
    verifier = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/components.mjs"
    _write(root / verifier, {"controlled_verifier_fixture": True})
    document["verifier_sources"][verifier] = _sha(root / verifier)
    receipt = retain(
        "observations/sample-chronology.json",
        {
            "status": "PASS",
            "runtime_errors": [],
            "browser": {"product": "Chrome/155.0.8059.40"},
            "verifier_sha256": _sha(root / verifier),
            "served_files_sha256": {"map.json": _sha(directory / "served/map.json")},
        },
    )
    document["cases"].append(
        {
            "case_id": "sample-owned-chronology-components",
            "generation": generation,
            "receipt": receipt,
            "source_candidate": current.CURRENT_SOURCE_CANDIDATE,
            "served_files": {"map.json": "served/map.json"},
            "native_execution": {
                "native_exit": 0,
                "timeout": False,
                "actual_argv": ["node", verifier],
            },
        }
    )
    stages = []
    document["generator_executions"].append(
        {"id": "generate-sample-chronology", "native_exit": 0, "timeout": False}
    )
    for execution in document["generator_executions"]:
        execution.update(
            actual_argv=["python", "controlled-fixture-generator"],
            stdout_sha256="a" * 64,
            stderr_sha256="b" * 64,
        )
        stages.append({**execution, "passed": True})
    for case in document["cases"]:
        case["source_candidate"] = current.CURRENT_SOURCE_CANDIDATE
        case["native_execution"].update(
            id="capture-" + case["case_id"],
            stdout_sha256="a" * 64,
            stderr_sha256="b" * 64,
        )
        stages.append(
            {
                **case["native_execution"],
                "passed": True,
                "browser_receipt": {"sha256": _sha(directory / case["receipt"])},
            }
        )
    document["native_terminal"] = retain(
        "native-terminal.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "native_exit": 0,
            "status": "passed",
            "resource_bounds_met": True,
            "stages": stages,
        },
    )
    document["native_plan"] = retain(
        "execution/plan.json", {"controlled_source_plan": True}
    )
    review = retain(
        "independent-review.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "qualified_current_plan_sha256": _sha(directory / document["native_plan"]),
            "qualified_current_terminal_sha256": _sha(
                directory / document["native_terminal"]
            ),
            "counts": {
                "successful_probes": 9,
                "visually_inspected_PNGs": 12,
                "authentic_component_source_sample_rows": 55,
                "normalized_sample_chronologies_checked": 55,
                "authentic_disjoint_components": 3,
                "native_browser_viewports": 2,
            },
            "served_and_output_hashes_all_match": True,
            "all_selected_source_tables_exact": True,
        },
    )
    document["independent_review"] = {"member": review}
    source_plan = retain(
        "source-normalization/plan.json", {"controlled_source_transport": True}
    )
    document["source_normalization_reference"] = {
        "plan": source_plan,
        "terminal": retain(
            "source-normalization/terminal.json",
            {
                "native_exit_code": 0,
                "status": "passed",
                "protected_inputs_unchanged": True,
                "plan_sha256": _sha(directory / source_plan),
            },
        ),
        "producer": retain(
            "source-normalization/producer.json",
            {"human_records": 1231, "animal_records": 1468},
        ),
        "observer": retain(
            "source-normalization/observer.json",
            {
                "native_exit": 0,
                "counts": {"samples": 2699},
                "exact_cross_format_chronology_native_identity_and_provenance": True,
            },
        ),
        "human-sweden": retain("source-normalization/human-sweden.json", []),
        "human-denmark": retain("source-normalization/human-denmark.json", []),
    }
    producer_stage = {
        "name": "maintained-source-owned-locality-wire-products",
        "actual_argv": ["python", "controlled-locality-producer"],
        "native_exit_code": 0,
        "timed_out": False,
    }
    source_directory = str(root)
    producer_plan = retain(
        "source-producer/plan.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "source_directory": source_directory,
            "stages": [
                {"name": producer_stage["name"], "argv": producer_stage["actual_argv"]},
                {
                    "name": "controlled-reader-predecessor",
                    "argv": ["python", "controlled-reader-predecessor"],
                },
                {
                    "name": "controlled-observer-predecessor",
                    "argv": ["python", "controlled-observer-predecessor"],
                },
            ],
        },
    )
    producer_terminal = retain(
        "source-producer/terminal.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "native_exit_code": 1,
            "status": "failed",
            "protected_inputs_unchanged": True,
            "plan_sha256": _sha(directory / producer_plan),
            "stages": [
                producer_stage,
                {
                    "name": "controlled-reader-predecessor",
                    "actual_argv": ["python", "controlled-reader-predecessor"],
                    "native_exit_code": 1,
                    "timed_out": False,
                },
            ],
        },
    )
    origins = retain(
        "source-producer/producer-import-origins.json",
        {
            "native_exit": 0,
            "source_root": source_directory,
            "actual_origins": [
                {
                    "module": "controlled_source",
                    "path": str(root / "source.txt"),
                    "sha256": _sha(root / "source.txt"),
                },
            ],
        },
    )
    locality_producer = retain(
        "current-reader/locality-producer.json",
        {
            "native_exit": 0,
            "animal_localities": 547,
            "human_selected_localities": 2,
            "animal_source_samples": 1468,
            "human_source_samples": 55,
        },
    )
    reader_proof = retain(
        "current-reader/reader.json",
        {
            "native_exit": 0,
            "actual_sample_records": 2699,
            "new_locality_records": 549,
            "new_locality_producer_proof_sha256": _sha(directory / locality_producer),
        },
    )
    observer_proof = retain(
        "current-reader/observer.json",
        {
            "native_exit": 0,
            "actual_original_samples": 2699,
            "locality_producer_sha256": _sha(directory / locality_producer),
            "reader_proof_sha256": _sha(directory / reader_proof),
            "original_sample_producer_sha256": _sha(
                directory / document["source_normalization_reference"]["producer"]
            ),
            "all_reader_cases_joined_to_exact_source_membership": True,
        },
    )
    reader_stages = [
        {
            "name": "actual-declared-public-reader-transport",
            "argv": ["python", "controlled-reader"],
        },
        {
            "name": "independent-original-membership-reader-observer",
            "argv": ["python", "controlled-observer"],
        },
    ]
    reader_plan = retain(
        "current-reader/plan.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "source_directory": source_directory,
            "stages": reader_stages,
            "reused_source_producer": {
                "original_plan_sha256": _sha(directory / producer_plan),
                "original_terminal_sha256": _sha(directory / producer_terminal),
                "reused_source_producer_proof_sha256": _sha(
                    directory / locality_producer
                ),
                "reused_source_producer_stage": producer_stage,
                "source_directory": source_directory,
            },
        },
    )
    reader_terminal = retain(
        "current-reader/terminal.json",
        {
            "candidate": current.CURRENT_SOURCE_CANDIDATE,
            "plan_sha256": _sha(directory / reader_plan),
            "native_exit_code": 0,
            "status": "passed",
            "protected_inputs_unchanged": True,
            "stages": [
                {
                    "name": stage["name"],
                    "actual_argv": stage["argv"],
                    "native_exit_code": 0,
                    "timed_out": False,
                }
                for stage in reader_stages
            ],
        },
    )
    document["current_reader_reference"] = {
        "plan": reader_plan,
        "terminal": reader_terminal,
        "locality-producer": locality_producer,
        "reader": reader_proof,
        "observer": observer_proof,
    }
    document["reused_source_producer_reference"] = {
        "plan": producer_plan,
        "terminal": producer_terminal,
        "producer-import-origins": origins,
    }
    review_payload = json.loads((directory / review).read_bytes())
    for group in ("current_reader_reference", "reused_source_producer_reference"):
        review_payload[group] = {
            role: {"path": str(directory / member), "sha256": _sha(directory / member)}
            for role, member in document[group].items()
        }
    retain(review, review_payload)
    generated_name = GENERATED_MEMBER.removeprefix("source/")
    generated_sha = document["source_footprint"].pop(generated_name)
    document["source_members"].pop(generated_name)
    document["runtime_resources"] = {
        generated_name: {
            "member": GENERATED_MEMBER,
            "sha256": generated_sha,
            "generated_by": "vcs-versioning",
        }
    }
    git_bodies = dict(_STATES[root].bodies)
    for i in range(387, 1159):
        name = (
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
            f"fixture_{i:04}.py"
        )
        raw = ("# own synthetic source " + name + "\n").encode()
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        git_bodies[name] = raw
        member = "source/" + name
        digest = hashlib.sha256(raw).hexdigest()
        document["files"].append({"path": member, "sha256": digest, "bytes": len(raw)})
        document["source_footprint"][name] = digest
        document["source_members"][name] = member
    for i in (52, 53):
        name = f"docs/report/fixture/source-{i}.json"
        value = {"own_source": i}
        _write(root / name, value)
        member = retain("source/" + name, value)
        document["source_footprint"][name] = _sha(root / name)
        document["source_members"][name] = member
    for i in range(1472 - len(document["files"])):
        retain(f"current-products/fixture/member-{i}.json", {"own_product": i})
    assert len(git_bodies) == 1171
    assert len(document["source_footprint"]) == 1226
    assert len(document["files"]) == 1472
    assert len(document["cases"]) == 9
    assert len(document["generations"]) == len(document["generator_executions"]) == 5
    assert len(document["products"]) == 43
    manifest = root / current.CURRENT_CAPTURE_PATH
    _write(manifest, document)
    _install_transport(
        root,
        git_bodies,
        monkeypatch,
        capture_path=current.CURRENT_CAPTURE_PATH,
        source_candidate=current.CURRENT_SOURCE_CANDIDATE,
        package_members=1165,
    )
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    monkeypatch.setattr(publication, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    _write(
        selector,
        {
            "schema_version": publication.CURRENT_SELECTOR_SCHEMA,
            "profile": publication.CURRENT_PROFILE,
            "owner_id": document["products"][0]["owner_id"],
            "capture_sha256": _sha(manifest),
        },
    )
    return root, selector, document


def test_current_profile_requires_complete_native_scope_and_preserves_historical(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, selector, document = sample_chronology_packet
    assert current.validated_sample_chronology_capture(root).document == document
    assert (
        capture.validated_atlas_source_views(root).document["schema_version"]
        == "atlas-source-view-native-capture.v1"
    )
    assert publication.build_capture_products(root, selector)


@pytest.mark.parametrize(
    "mutation", ["unknown_profile", "old_schema_with_new_fields", "missing_profile"]
)
def test_current_selector_refuses_unknown_or_ambiguous_profile(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    root, selector, _ = sample_chronology_packet
    selected = json.loads(selector.read_bytes())
    if mutation == "unknown_profile":
        selected["profile"] = "unreviewed-source"
    elif mutation == "old_schema_with_new_fields":
        selected["schema_version"] = publication.SELECTOR_SCHEMA
    else:
        del selected["profile"]
    _write(selector, selected)
    with pytest.raises(ReportRebuildError):
        publication.build_capture_products(root, selector)


def test_current_source_byte_change_is_refused_without_compatibility_waiver(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, _ = sample_chronology_packet
    (root / "source.txt").write_text("controlled source\n\n", encoding="utf-8")
    with pytest.raises(ReportRebuildError, match="current source footprint differs"):
        current.validated_sample_chronology_capture(root)


@pytest.mark.parametrize(
    "mutation", ["incomplete_scope", "failed_native_stage", "different_case_argv"]
)
def test_current_profile_refuses_incomplete_failed_or_unbound_native_lineage(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, document = sample_chronology_packet
    directory = root / Path(current.CURRENT_CAPTURE_PATH).parent
    native_path = directory / document["native_terminal"]
    native = json.loads(native_path.read_bytes())
    if mutation == "incomplete_scope":
        native["stages"].pop()
    elif mutation == "failed_native_stage":
        native["stages"][-1]["native_exit"] = 1
        native["stages"][-1]["passed"] = False
    else:
        document["cases"][-1]["native_execution"]["actual_argv"][0] = "different-node"
    _write(native_path, native)
    for row in document["files"]:
        if row["path"] == document["native_terminal"]:
            row.update(sha256=_sha(native_path), bytes=native_path.stat().st_size)
    manifest = root / current.CURRENT_CAPTURE_PATH
    _write(manifest, document)
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    with pytest.raises(ReportRebuildError):
        current.validated_sample_chronology_capture(root)


@pytest.mark.parametrize(
    "change", ["current_version", "captured_version", "unknown_resource"]
)
def test_current_profile_separates_generated_runtime_from_maintained_source(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, document = sample_chronology_packet
    resource_path = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
    )
    resource = document["runtime_resources"][resource_path]
    _write(root / resource_path, {"different_current_generated_version": True})
    if change == "captured_version":
        resource["sha256"] = "0" * 64
    elif change == "unknown_resource":
        document["runtime_resources"] = {"maintained_source.py": resource}
    manifest = root / current.CURRENT_CAPTURE_PATH
    _write(manifest, document)
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    if change == "current_version":
        current.validated_sample_chronology_capture(root)
    else:
        with pytest.raises((ReportRebuildError, ValueError)):
            current.validated_sample_chronology_capture(root)


@pytest.mark.parametrize(
    "binding", ["qualified_current_plan_sha256", "qualified_current_terminal_sha256"]
)
def test_current_profile_refuses_review_from_another_native_execution(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    binding: str,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, document = sample_chronology_packet
    directory = (root / current.CURRENT_CAPTURE_PATH).parent
    member = document["independent_review"]["member"]
    review_path = directory / member
    review = json.loads(review_path.read_bytes())
    review[binding] = "0" * 64
    _write(review_path, review)
    for row in document["files"]:
        if row["path"] == member:
            row.update(sha256=_sha(review_path), bytes=review_path.stat().st_size)
    manifest = root / current.CURRENT_CAPTURE_PATH
    _write(manifest, document)
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    with pytest.raises(
        ReportRebuildError, match="review native execution binding differs"
    ):
        current.validated_sample_chronology_capture(root)


@pytest.mark.parametrize(
    "mutation", ["native_failure", "boolean_exit", "wrong_plan", "wrong_population"]
)
def test_current_profile_requires_qualified_source_normalization_transport(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, document = sample_chronology_packet
    directory = (root / current.CURRENT_CAPTURE_PATH).parent
    member = document["source_normalization_reference"][
        "producer" if mutation == "wrong_population" else "terminal"
    ]
    path = directory / member
    payload = json.loads(path.read_bytes())
    if mutation == "native_failure":
        payload["native_exit_code"] = 1
    elif mutation == "boolean_exit":
        payload["native_exit_code"] = False
    elif mutation == "wrong_plan":
        payload["plan_sha256"] = "0" * 64
    else:
        payload["human_records"] = 1230
    _write(path, payload)
    for row in document["files"]:
        if row["path"] == member:
            row.update(sha256=_sha(path), bytes=path.stat().st_size)
    manifest = root / current.CURRENT_CAPTURE_PATH
    _write(manifest, document)
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(manifest))
    with pytest.raises(
        ReportRebuildError, match="source normalization native proof differs"
    ):
        current.validated_sample_chronology_capture(root)


@pytest.mark.parametrize("fixture_name", ["packet", "sample_chronology_packet"])
@pytest.mark.parametrize(
    "operation,owner_id",
    [
        ("keyless-identity", "atlas/keyless-cache-matrix/candidate-identity"),
        ("provider-review", "atlas/provider-accessibility/browser-evidence"),
        ("modeled-review", "atlas/modeled-panel-browser/browser-evidence"),
    ],
)
def test_projected_metadata_preserves_exact_capture_source_epoch(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    fixture_name: str,
    operation: str,
    owner_id: str,
) -> None:
    """Every derived metadata surface names its admitted packet path and digest."""
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    controlled: tuple[Path, Path, dict[str, Any]] = request.getfixturevalue(
        fixture_name
    )
    root, selector, document = controlled
    product = next(row for row in document["products"] if row["owner_id"] == owner_id)
    product["operation"] = operation
    product.pop("source")
    is_current = fixture_name == "sample_chronology_packet"
    capture_path = current.CURRENT_CAPTURE_PATH if is_current else capture.CAPTURE_PATH
    manifest = root / capture_path
    _write(manifest, document)
    digest = _sha(manifest)
    if is_current:
        _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
        monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", digest)
        monkeypatch.setattr(publication, "CURRENT_CAPTURE_SHA256", digest)
        selection = {
            "schema_version": publication.CURRENT_SELECTOR_SCHEMA,
            "profile": publication.CURRENT_PROFILE,
            "owner_id": owner_id,
            "capture_sha256": digest,
        }
    else:
        _refresh_transport(root, monkeypatch)
        monkeypatch.setattr(capture, "CAPTURE_SHA256", digest)
        monkeypatch.setattr(publication, "CAPTURE_SHA256", digest)
        selection = {
            "schema_version": publication.SELECTOR_SCHEMA,
            "owner_id": owner_id,
            "capture_sha256": digest,
        }
    _write(selector, selection)
    raw = publication.build_capture_products(root, selector)[product["output_path"]]
    source = json.loads(raw)["source_capture"]
    assert source["capture_path"] == capture_path
    assert source["capture_sha256"] == digest
    assert source["source_candidate"] == document["source_candidate"]
    assert source["browser_executed_by_this_projection"] is False
    assert source["numerical_execution"] is False
    assert source["scientific_admission"] is False


@pytest.mark.parametrize("declaration", [None, False, 1])
def test_current_profile_requires_explicit_owned_source_context(
    sample_chronology_packet: tuple[Path, Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    declaration: object,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as current,
    )

    root, _, document = sample_chronology_packet
    if declaration is None:
        document["source_context"].pop("not_a_clean_git_tree")
    else:
        document["source_context"]["not_a_clean_git_tree"] = declaration
    path = root / current.CURRENT_CAPTURE_PATH
    _write(path, document)
    _refresh_transport(root, monkeypatch, current.CURRENT_CAPTURE_PATH)
    monkeypatch.setattr(current, "CURRENT_CAPTURE_SHA256", _sha(path))
    with pytest.raises(
        ReportRebuildError, match="selected-source/browser scope differs"
    ):
        current.validated_sample_chronology_capture(root)
