from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from bijux_pollenomics.collection.contracts.capabilities import (
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
    SEAD_NORMALIZED_EVIDENCE_MANIFEST,
    build_source_capability_audit_payload,
)
from bijux_pollenomics.collection.contracts.capabilities import (
    receipts as receipt_validation,
)
from bijux_pollenomics.collection.contracts.capabilities import sead as sead_validation
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

from .support import REPO_ROOT, _write_full_sead_admission_fixture


def test_aadr_receipt_rejects_same_size_artifact_substitution() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        release_root = output_root / "aadr/v66"
        first_path = release_root / "1240k/example.anno"
        second_path = release_root / "ho/example-ho.anno"
        first_path.parent.mkdir(parents=True)
        second_path.parent.mkdir(parents=True)
        first_path.write_bytes(b"id\tvalue\none\talpha\n")
        second_path.write_bytes(b"id\tvalue\ntwo\tbeta\n")
        manifest_path = release_root / "release_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "source": "AADR",
                    "downloaded_files": [
                        "1240k/example.anno",
                        "ho/example-ho.anno",
                    ],
                    "anno_files": [
                        {
                            "filename": first_path.name,
                            "filesize": first_path.stat().st_size,
                            "md5": hashlib.md5(
                                first_path.read_bytes(), usedforsecurity=False
                            ).hexdigest(),
                        },
                        {
                            "filename": second_path.name,
                            "filesize": second_path.stat().st_size,
                            "md5": hashlib.md5(
                                second_path.read_bytes(), usedforsecurity=False
                            ).hexdigest(),
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        before = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )
        first_path.write_bytes(b"id\tvalue\none\tomega\n")
        after = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    before_rows = {(row["source_key"], row["dimension"]): row for row in before["rows"]}
    after_rows = {(row["source_key"], row["dimension"]): row for row in after["rows"]}
    assert before_rows[("aadr", "dataset_provenance")]["materialization"] == (
        "complete"
    )
    assert after_rows[("aadr", "dataset_provenance")]["materialization"] == ("missing")


def test_sead_admission_rejects_same_size_payload_substitution(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        _, payload_path = _write_full_sead_admission_fixture(output_root, payload_bytes)
        monkeypatch.setattr(
            sead_validation, "_valid_sead_admission", lambda _path: True
        )

        before = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )
        payload_path.write_bytes(payload_bytes.replace(b'"site_id":1', b'"site_id":2'))
        after = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    before_rows = {(row["source_key"], row["dimension"]): row for row in before["rows"]}
    after_rows = {(row["source_key"], row["dimension"]): row for row in after["rows"]}
    assert before_rows[("sead", "site_identity")]["materialization"] == "complete"
    assert after_rows[("sead", "site_identity")]["materialization"] == "partial"
    assert any(
        path.endswith("/payloads/tbl_sites.json")
        for path in after_rows[("sead", "site_identity")]["missing_evidence_paths"]
    )


def test_sead_admission_rejects_incomplete_declared_file_set() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        admission_path, _ = _write_full_sead_admission_fixture(
            output_root, payload_bytes
        )

        audit = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

        row = next(
            row
            for row in audit["rows"]
            if row["source_key"] == "sead" and row["dimension"] == "site_identity"
        )
        assert not sead_validation._valid_sead_admission(admission_path)
        assert row["materialization"] != "complete"
        assert SEAD_ADMITTED_ACQUISITION_ADMISSION in row["missing_evidence_paths"]


def test_sead_admission_rejects_payload_and_admission_rewrite() -> None:
    source_root = (REPO_ROOT / SEAD_ADMITTED_ACQUISITION_ADMISSION).parent
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "artifacts") as temporary:
        destination = Path(temporary) / source_root.name
        shutil.copytree(source_root, destination, copy_function=os.link)
        admission_path = destination / "admission.json"
        payload_path = destination / "payloads/tbl_sites.json"
        assert sead_validation._valid_sead_admission(admission_path)

        payload_bytes = payload_path.read_bytes()
        changed_bytes = payload_bytes.replace(b'"site_id":1,', b'"site_id":2,', 1)
        assert changed_bytes != payload_bytes
        payload_path.unlink()
        payload_path.write_bytes(changed_bytes)
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        record = next(
            item
            for item in admission["copied_files"]
            if item["path"] == "payloads/tbl_sites.json"
        )
        record["byte_count"] = len(changed_bytes)
        record["sha256"] = hashlib.sha256(changed_bytes).hexdigest()
        admission_path.unlink()
        admission_path.write_text(
            json.dumps(admission, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        assert not sead_validation._valid_sead_admission(admission_path)


def test_sead_normalized_evidence_rejects_raw_digest_divergence() -> None:
    normalized_source = REPO_ROOT / SEAD_NORMALIZED_EVIDENCE_MANIFEST
    raw_source = REPO_ROOT / SEAD_ADMITTED_ACQUISITION_ADMISSION
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "artifacts") as temporary:
        data_root = Path(temporary) / "data"
        normalized_root = (
            data_root / SEAD_NORMALIZED_EVIDENCE_MANIFEST.removeprefix("data/")
        ).parent
        raw_root = (
            data_root / SEAD_ADMITTED_ACQUISITION_ADMISSION.removeprefix("data/")
        ).parent
        shutil.copytree(
            normalized_source.parent, normalized_root, copy_function=os.link
        )
        shutil.copytree(raw_source.parent, raw_root, copy_function=os.link)
        manifest_path = normalized_root / "evidence_materialization_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert sead_validation._valid_sead_normalized_admission_link(
            manifest_path, manifest
        )

        relation_path = normalized_root / "observation_relation_index.json"
        relations = json.loads(relation_path.read_text(encoding="utf-8"))
        relations["source_table_sha256"]["tbl_sites"] = "0" * 64
        relation_path.unlink()
        relation_path.write_text(
            json.dumps(relations, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        assert not sead_validation._valid_sead_normalized_admission_link(
            manifest_path, manifest
        )


def test_sead_admission_rejects_the_obsolete_19_table_25_join_scope() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        admission_path, _ = _write_full_sead_admission_fixture(
            output_root, payload_bytes
        )
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        admission["declared_scope"].update(
            {
                "scope_key": "declared_chronology_relations",
                "table_count": 19,
                "join_count": 25,
                "tables": list(SEAD_FULL_EVIDENCE_SOURCE_TABLES[:19]),
            }
        )
        admission_path.write_text(json.dumps(admission), encoding="utf-8")

        assert not sead_validation._valid_sead_admission(admission_path)


def test_receipt_validators_reject_traversal_and_symlink_artifacts() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        outside = root / "outside.bin"
        outside.write_bytes(b"governed bytes")

        landclim_root = root / "landclim"
        landclim_root.mkdir()
        linked_asset = landclim_root / "linked.bin"
        linked_asset.symlink_to(outside)
        landclim_payload = {
            "schema_version": "landclim-raw-receipt.v1",
            "source": "LandClim",
            "asset_count": 1,
            "assets": [
                {
                    "filename": linked_asset.name,
                    "size_bytes": outside.stat().st_size,
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                }
            ],
        }
        assert not receipt_validation._valid_landclim_receipt(
            landclim_root / "receipt.json", landclim_payload
        )

        boundary_root = root / "boundaries/raw"
        boundary_root.mkdir(parents=True)
        boundary_payload = {
            "schema_version": "natural-earth-boundary-receipt.v1",
            "source": "Natural Earth",
            "country_artifacts": {
                country: {
                    "path": "../../outside.bin",
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    "feature_count": 1,
                }
                for country in ("Sweden", "Denmark", "Norway", "Finland")
            },
            "normalized_artifact": {
                "path": "../../outside.bin",
                "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                "feature_count": 4,
            },
        }
        assert not receipt_validation._valid_boundary_receipt(
            boundary_root / "receipt.json", boundary_payload
        )

        aadr_root = root / "aadr"
        (aadr_root / "1240k").mkdir(parents=True)
        aadr_link = aadr_root / "1240k/linked.anno"
        aadr_link.symlink_to(outside)
        aadr_payload = {
            "source": "AADR",
            "downloaded_files": ["1240k/linked.anno"],
            "anno_files": [
                {
                    "filename": aadr_link.name,
                    "filesize": outside.stat().st_size,
                    "md5": hashlib.md5(
                        outside.read_bytes(), usedforsecurity=False
                    ).hexdigest(),
                }
            ],
        }
        assert not receipt_validation._valid_aadr_receipt(
            aadr_root / "release_manifest.json", aadr_payload
        )
