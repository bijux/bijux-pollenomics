"""Check the publisher receipt and configured Namibian source-row route."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.vegetation import namibia_source_join

DESCRIPTOR = Path("configs/ci/qualified-report-sources/namibia.json")
SOURCE_ID = "vegetation/namibia-modern-pollen-vegetation"
PARENT_DOI = "10.1594/PANGAEA.931037"
LICENSE = (
    "License:\tCreative Commons Attribution 4.0 International (CC-BY-4.0) "
    "(URI: https://creativecommons.org/licenses/by/4.0/)"
)
NAMES = ("PANGAEA.931033.tab", "PANGAEA.931035.tab")
COLUMNS = (("Event", "Aca [#]"), ("Event", "Ring sect radius [m]"))


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _packet(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()
    root = tmp_path / "source-store"
    directory = root / SOURCE_ID
    directory.mkdir(parents=True)
    files: list[dict[str, object]] = []
    receipt_files: dict[str, object] = {}
    for name, columns in zip(NAMES, COLUMNS, strict=True):
        doi = "10.1594/" + name.removesuffix(".tab")
        url = f"https://doi.pangaea.de/{doi}?format=textfile"
        payload = (
            "/* DATA DESCRIPTION:\n"
            f"Citation:\tSynthetic publisher test https://doi.org/{doi}\n"
            f"\tIn: synthetic series https://doi.org/{PARENT_DOI}\n"
            f"{LICENSE}\n"
            "*/\n" + "\t".join(columns) + "\nsite\t1\n"
        ).encode()
        (directory / name).write_bytes(payload)
        files.append(
            {
                "path": name,
                "sha256": _sha(payload),
                "size": len(payload),
                "doi": doi,
                "url": url,
                "columns": list(columns),
            }
        )
        receipt_files[name] = {
            "sha256": _sha(payload),
            "bytes": len(payload),
            "url": url,
        }
    identity = {
        "source": "Synthetic pair; parent PANGAEA.931037",
        "rights": "CC BY 4.0 as stated in original headers",
        "retrieved_utc": "2026-10-01 18:14:30 UTC",
    }
    receipt = {**identity, "files": receipt_files}
    custody = directory / "source_manifest.json"
    _json(custody, receipt)
    descriptor = {
        "schema_version": "qualified-publisher-report-tables.v1",
        "source_id": SOURCE_ID,
        "parent_doi": PARENT_DOI,
        "license": "CC-BY-4.0",
        **identity,
        "custody": {
            "path": custody.name,
            "sha256": _sha(custody.read_bytes()),
            "size": custody.stat().st_size,
        },
        "files": files,
    }
    _json(repository / DESCRIPTOR, descriptor)
    return repository, root, descriptor


def test_publisher_pair_is_qualified_without_copy(tmp_path: Path) -> None:
    repository, root, _ = _packet(tmp_path)
    before = sorted(path.relative_to(repository) for path in repository.rglob("*"))
    qualified = validated_external_report_sources(repository, root, DESCRIPTOR)
    assert qualified.directory == root / SOURCE_ID
    assert set(qualified.inputs) == {
        DESCRIPTOR.as_posix(),
        f"external/{SOURCE_ID}/source_manifest.json",
        *(f"external/{SOURCE_ID}/{name}" for name in NAMES),
    }
    assert (
        sorted(path.relative_to(repository) for path in repository.rglob("*")) == before
    )


@pytest.mark.parametrize(
    "change",
    [
        "unknown-schema",
        "receipt-bytes",
        "rights",
        "url",
        "size",
        "sha",
        "doi",
        "columns",
        "license",
        "parent",
        "extra-row",
    ],
)
def test_publisher_identity_mismatch_refuses(tmp_path: Path, change: str) -> None:
    repository, root, descriptor = _packet(tmp_path)
    source = root / SOURCE_ID / NAMES[0]
    if change == "unknown-schema":
        descriptor["schema_version"] = "unknown"
    elif change == "receipt-bytes":
        receipt = root / SOURCE_ID / "source_manifest.json"
        receipt.write_bytes(receipt.read_bytes() + b" ")
    elif change == "rights":
        descriptor["rights"] = "CC BY 4.0 but different custody"
    elif change == "url":
        descriptor["files"][0]["url"] = "https://example.org/other"
    elif change == "size":
        descriptor["files"][0]["size"] += 1
    elif change == "sha":
        source.write_bytes(source.read_bytes() + b"changed\n")
    elif change == "doi":
        descriptor["files"][0]["doi"] = "10.1594/PANGAEA.999999"
    elif change == "columns":
        descriptor["files"][0]["columns"] = ["Event", "wrong"]
    elif change == "license":
        source.write_bytes(
            source.read_bytes().replace(LICENSE.encode(), b"License:\tunknown")
        )
    elif change == "parent":
        source.write_bytes(
            source.read_bytes().replace(PARENT_DOI.encode(), b"10.1594/PANGAEA.000001")
        )
    else:
        receipt = root / SOURCE_ID / "source_manifest.json"
        value = json.loads(receipt.read_text())
        value["files"]["unreviewed.tab"] = value["files"][NAMES[0]]
        _json(receipt, value)
        descriptor["custody"]["sha256"] = _sha(receipt.read_bytes())
        descriptor["custody"]["size"] = receipt.stat().st_size
    _json(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, root, DESCRIPTOR)


def test_nonreal_source_ancestor_refuses(tmp_path: Path) -> None:
    repository, root, _ = _packet(tmp_path)
    moved = root.with_name("moved-store")
    root.rename(moved)
    root.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real|regular"):
        validated_external_report_sources(repository, root, DESCRIPTOR)


@pytest.mark.parametrize("change", ["dataset-doi", "parent-doi", "license", "columns"])
def test_primary_header_still_refuses_when_receipt_and_digest_are_rewritten(
    tmp_path: Path, change: str
) -> None:
    repository, root, descriptor = _packet(tmp_path)
    directory = root / SOURCE_ID
    source = directory / NAMES[0]
    payload = source.read_bytes()
    if change == "dataset-doi":
        payload = payload.replace(
            b"https://doi.org/10.1594/PANGAEA.931033",
            b"https://doi.org/10.1594/PANGAEA.999999",
        )
    elif change == "parent-doi":
        payload = payload.replace(PARENT_DOI.encode(), b"10.1594/PANGAEA.999999")
    elif change == "license":
        payload = payload.replace(LICENSE.encode(), b"License:\tunknown")
    else:
        payload = payload.replace(b"Event\tAca [#]", b"Event\tOther [#]")
    source.write_bytes(payload)
    descriptor["files"][0]["sha256"] = _sha(payload)
    descriptor["files"][0]["size"] = len(payload)
    receipt_path = directory / "source_manifest.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["files"][NAMES[0]]["sha256"] = _sha(payload)
    receipt["files"][NAMES[0]]["bytes"] = len(payload)
    _json(receipt_path, receipt)
    descriptor["custody"]["sha256"] = _sha(receipt_path.read_bytes())
    descriptor["custody"]["size"] = receipt_path.stat().st_size
    _json(repository / DESCRIPTOR, descriptor)
    with pytest.raises(ReportRebuildError, match="publisher table .* differ"):
        validated_external_report_sources(repository, root, DESCRIPTOR)


def test_wrapper_binds_forwarded_descriptor_and_absent_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, descriptor = _packet(tmp_path)
    replay_path = repository / namibia_source_join.REPLAY
    replay_path.parent.mkdir(parents=True)
    replay_path.write_text(
        "from pathlib import Path\nimport sys\n"
        f"SOURCES = {repr({row['path']: row['sha256'] for row in descriptor['files']})}\n"
        f"POLLEN_COLUMNS = {repr(tuple(descriptor['files'][0]['columns']))}\n"
        f"VEGETATION_COLUMNS = {repr(tuple(descriptor['files'][1]['columns']))}\n"
        "def main():\n"
        "    args = sys.argv\n"
        "    out = Path(args[args.index('--output-dir') + 1])\n"
        "    source = Path(args[args.index('--source-dir') + 1])\n"
        "    out.mkdir(parents=True)\n"
        "    (out / 'paired.csv').write_text(str(source) + '\\n')\n"
        "    (out / 'report.json').write_text('{}\\n')\n"
    )
    monkeypatch.setattr(
        namibia_source_join, "REPLAY_SHA256", _sha(replay_path.read_bytes())
    )
    monkeypatch.setattr(namibia_source_join, "SOURCE_ID", SOURCE_ID)
    output = repository / "artifacts/source-products"
    assert (
        namibia_source_join.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(root),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert (output / "paired.csv").read_text() == str(root / SOURCE_ID) + "\n"
    with pytest.raises(ReportRebuildError, match="absent"):
        namibia_source_join.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(root),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--output",
                str(output),
            ]
        )


def test_wrapper_refuses_changed_replay_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, _ = _packet(tmp_path)
    replay_path = repository / namibia_source_join.REPLAY
    replay_path.parent.mkdir(parents=True)
    replay_path.write_text("raise AssertionError('unreviewed producer ran')\n")
    monkeypatch.setattr(namibia_source_join, "REPLAY_SHA256", "0" * 64)
    output = repository / "artifacts/source-products"
    with pytest.raises(ReportRebuildError, match="replay read set changed"):
        namibia_source_join.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(root),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--output",
                str(output),
            ]
        )
    assert not output.exists()
