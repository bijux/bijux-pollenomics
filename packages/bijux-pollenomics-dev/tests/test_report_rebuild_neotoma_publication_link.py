"""Refuse changed Neotoma publication-link custody before preparation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import neotoma_publication_link as QUAL
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion import (
    lilla_gloppsjon_direct_pollen as ORIG,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    lilla_gloppsjon_preparation as WRAP,
)

DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/lilla-gloppsjon-publication-link.json"
)
SOURCE_ID = "neotoma/publication-links/2026-09-29"
RESPONSE = "responses/dataset-4200-publications.json"


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packet(tmp_path: Path) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    repository.mkdir()
    source_root = tmp_path / "source-store"
    source = source_root / SOURCE_ID
    (source / "responses").mkdir(parents=True)
    primary = {
        "publicationid": 16060,
        "datasets": [{"siteid": 3234, "datasetid": 4200, "primary": True}],
    }
    response_bytes = encoded({"data": [{"publication": primary}]})
    (source / RESPONSE).write_bytes(response_bytes)
    rows: list[dict[str, object]] = [
        {"path": f"responses/dataset-{number}-publications.json"}
        for number in range(1, 169)
    ]
    rows.append(
        {
            "path": RESPONSE,
            "dataset_id": 4200,
            "http_status": 200,
            "sha256": sha(response_bytes),
            "bytes": len(response_bytes),
            "url": f"{QUAL.SOURCE_API}4200/publications",
        }
    )
    manifest_bytes = encoded(
        {
            "schema_version": "neotoma-candidate-publication-capture.v1",
            "source_api": QUAL.SOURCE_API,
            "response_count": 169,
            "responses": rows,
        }
    )
    (source / "capture-manifest.json").write_bytes(manifest_bytes)
    descriptor = {
        "schema_version": QUAL.SCHEMA,
        "source_id": SOURCE_ID,
        "capture_manifest": {
            "path": "capture-manifest.json",
            "sha256": sha(manifest_bytes),
            "size": len(manifest_bytes),
        },
        "response": {
            "path": RESPONSE,
            "sha256": sha(response_bytes),
            "size": len(response_bytes),
        },
        "dataset_id": 4200,
        "publication_id": 16060,
        "source_api": QUAL.SOURCE_API,
        "response_count": 169,
    }
    descriptor_file = repository / DESCRIPTOR
    descriptor_file.parent.mkdir(parents=True)
    descriptor_file.write_bytes(encoded(descriptor))
    return repository, source_root, descriptor_file


def test_retained_capture_binds_one_response_without_copy(tmp_path: Path) -> None:
    repository, source_root, descriptor = packet(tmp_path)
    result = QUAL.validated_neotoma_publication_link(
        repository, source_root, DESCRIPTOR
    )
    assert result.descriptor_sha256 == sha(descriptor.read_bytes())
    assert len(result.inputs) == 3
    assert (
        result.inputs[f"external/{SOURCE_ID}/{RESPONSE}"]
        == source_root / SOURCE_ID / RESPONSE
    )
    assert not (repository / "external").exists()


@pytest.mark.parametrize(
    "change", ["response", "capture", "symlink", "primary", "duplicate"]
)
def test_capture_mutation_or_unsafe_path_refused(tmp_path: Path, change: str) -> None:
    repository, source_root, _ = packet(tmp_path)
    source = source_root / SOURCE_ID
    response = source / RESPONSE
    capture = source / "capture-manifest.json"
    if change == "response":
        response.write_bytes(response.read_bytes() + b" ")
    elif change == "capture":
        capture.write_bytes(capture.read_bytes() + b" ")
    elif change == "symlink":
        other = tmp_path / "other.json"
        other.write_bytes(response.read_bytes())
        response.unlink()
        response.symlink_to(other)
    elif change == "primary":
        content = json.loads(response.read_bytes())
        content["data"][0]["publication"]["datasets"][0]["primary"] = False
        payload = encoded(content)
        response.write_bytes(payload)
        descriptor = json.loads((repository / DESCRIPTOR).read_bytes())
        descriptor["response"].update(sha256=sha(payload), size=len(payload))
        (repository / DESCRIPTOR).write_bytes(encoded(descriptor))
        manifest = json.loads(capture.read_bytes())
        manifest["responses"][-1].update(sha256=sha(payload), bytes=len(payload))
        capture.write_bytes(encoded(manifest))
        descriptor["capture_manifest"].update(
            sha256=sha(capture.read_bytes()), size=capture.stat().st_size
        )
        (repository / DESCRIPTOR).write_bytes(encoded(descriptor))
    else:
        manifest = json.loads(capture.read_bytes())
        manifest["responses"][0]["path"] = RESPONSE
        capture.write_bytes(encoded(manifest))
        descriptor = json.loads((repository / DESCRIPTOR).read_bytes())
        descriptor["capture_manifest"].update(
            sha256=sha(capture.read_bytes()), size=capture.stat().st_size
        )
        (repository / DESCRIPTOR).write_bytes(encoded(descriptor))
    with pytest.raises(ReportRebuildError):
        QUAL.validated_neotoma_publication_link(repository, source_root, DESCRIPTOR)


def test_wrapper_passes_qualified_source_and_confines_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, _ = packet(tmp_path)
    family = repository / ORIG.PROTOCOL
    family.parent.mkdir(parents=True)
    family.write_bytes(
        encoded(
            {
                "publication_response_locator": f"bijux-pollenomics-data/{SOURCE_ID}/{RESPONSE}",
                "publication_response_sha256": sha(
                    (source_root / SOURCE_ID / RESPONSE).read_bytes()
                ),
                "source_metadata_sha256": {
                    "manifest.json": "x",
                    **{
                        f"surfaces/{name}/part-00001.json": "x"
                        for name in (
                            "sites",
                            "collection_units",
                            "datasets",
                            "samples",
                            "age_claims",
                            "chronologies",
                            "chronology_controls",
                        )
                    },
                },
                "training_profile_path": WRAP.TRAINING.as_posix(),
                "training_receipt_path": WRAP.TRAINING_RECEIPT.as_posix(),
            }
        )
    )
    for name in json.loads(family.read_bytes())["source_metadata_sha256"]:
        path = repository / ORIG.RELATIONAL / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source", encoding="utf-8")
    (repository / WRAP.TRAINING).parent.mkdir(parents=True)
    (repository / WRAP.TRAINING).write_bytes(b"training")
    (repository / WRAP.TRAINING_RECEIPT).write_text("receipt", encoding="utf-8")
    (repository / "artifacts").mkdir()
    output = repository / "artifacts/prepared"
    calls: list[Path] = []

    def fake_prepare(
        _repository: Path, stage: Path, *, publication_response: Path
    ) -> None:
        calls.append(publication_response)
        stage.mkdir()
        for name in WRAP.RESULTS:
            (stage / name).write_text(name, encoding="utf-8")

    monkeypatch.setattr(WRAP, "prepare", fake_prepare)
    WRAP.run(repository, source_root, DESCRIPTOR, output)
    assert calls == [source_root / SOURCE_ID / RESPONSE]
    assert {p.name for p in output.iterdir()} == WRAP.RESULTS
    with pytest.raises(ReportRebuildError):
        WRAP.run(repository, source_root, DESCRIPTOR, output)


def test_original_publication_guard_accepts_override(tmp_path: Path) -> None:
    repository, source_root, _ = packet(tmp_path)
    response = source_root / SOURCE_ID / RESPONSE
    protocol = {
        "publication_response_locator": "missing.json",
        "publication_response_sha256": sha(response.read_bytes()),
    }
    ORIG._verify_publication(repository, protocol, response)
    with pytest.raises((ValueError, FileNotFoundError)):
        ORIG._verify_publication(repository, protocol)


def test_wrapper_refuses_other_descriptor_before_qualification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, _ = packet(tmp_path)
    (repository / "artifacts").mkdir()

    def forbidden_qualification(*_args: object) -> None:
        raise AssertionError("unrequested source descriptor was read")

    monkeypatch.setattr(
        WRAP, "validated_external_report_sources", forbidden_qualification
    )
    with pytest.raises(ReportRebuildError, match="descriptor differs"):
        WRAP.run(
            repository,
            source_root,
            Path("configs/ci/qualified-report-sources/other.json"),
            repository / "artifacts/prepared",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("training_profile_path", "/outside/training.json.gz"),
        ("training_profile_path", "../outside/training.json.gz"),
        ("training_receipt_path", "/outside/receipt.json"),
        ("training_receipt_path", "../outside/receipt.json"),
        ("training_profile_path", "docs/report/other/training.json.gz"),
    ],
)
def test_wrapper_refuses_changed_training_source_before_prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    repository, source_root, _ = packet(tmp_path)
    protocol = repository / ORIG.PROTOCOL
    protocol.parent.mkdir(parents=True)
    protocol.write_bytes(
        encoded(
            {
                "publication_response_locator": f"bijux-pollenomics-data/{SOURCE_ID}/{RESPONSE}",
                "publication_response_sha256": sha(
                    (source_root / SOURCE_ID / RESPONSE).read_bytes()
                ),
                "source_metadata_sha256": {
                    "manifest.json": "x",
                    **{
                        f"surfaces/{name}/part-00001.json": "x"
                        for name in (
                            "sites",
                            "collection_units",
                            "datasets",
                            "samples",
                            "age_claims",
                            "chronologies",
                            "chronology_controls",
                        )
                    },
                },
                "training_profile_path": WRAP.TRAINING.as_posix(),
                "training_receipt_path": WRAP.TRAINING_RECEIPT.as_posix(),
            }
        )
    )
    changed = json.loads(protocol.read_bytes())
    changed[field] = value
    protocol.write_bytes(encoded(changed))
    for name in changed["source_metadata_sha256"]:
        path = repository / ORIG.RELATIONAL / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source", encoding="utf-8")
    (repository / "artifacts").mkdir()
    calls: list[Path] = []

    def forbidden_prepare(*args: Path, **kwargs: Path) -> None:
        calls.append(args[0])

    monkeypatch.setattr(WRAP, "prepare", forbidden_prepare)
    with pytest.raises(
        ReportRebuildError, match="safe relative path|training source differs"
    ):
        WRAP.run(repository, source_root, DESCRIPTOR, repository / "artifacts/prepared")
    assert calls == []
    assert not (repository / "artifacts/prepared").exists()
