"""Current single-core capture preservation and explicit source-change boundaries."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit

import pytest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics_dev.source_completion.neotoma import (
    capture_comparison as account,
)


def _row() -> dict[str, Any]:
    return {
        "site": {
            "siteid": 13338,
            "sitename": "Abborrtjärnen",
            "geography": None,
            "collectionunit": {
                "collectionunitid": 14910,
                "handle": "ABBO",
                "defaultchronology": 11516,
                "chronologies": [
                    {
                        "chronology": {
                            "chronologyid": 11516,
                            "chronology": {
                                "modelagetype": "Calibrated radiocarbon years BP",
                                "isdefault": True,
                            },
                            "chroncontrols": [
                                {
                                    "chroncontrolid": 7,
                                    "depth": 650,
                                    "chroncontrolage": 1200,
                                    "geochron": {
                                        "geochronage": 1250,
                                        "labnumber": "Lab-1",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "dataset": {
                    "datasetid": 19913,
                    "doi": ["10.21233/2vzb-bg61"],
                    "database": "European Pollen Database",
                    "datasetpi": [{"contactname": "Thomas Giesecke"}],
                    "samples": [
                        {
                            "sampleid": 173174,
                            "depth": 650,
                            "native_note": None,
                            "ages": [
                                {
                                    "chronologyid": 11516,
                                    "agetype": "Calibrated radiocarbon years BP",
                                    "age": 1200,
                                    "ageolder": None,
                                    "ageyounger": None,
                                }
                            ],
                            "datum": [
                                {
                                    "taxonid": 5,
                                    "variablename": "Pinus",
                                    "units": "NISP",
                                    "element": "pollen",
                                    "value": 0,
                                },
                                {
                                    "taxonid": 6,
                                    "variablename": "Betula",
                                    "units": "NISP",
                                    "element": "pollen",
                                    "value": None,
                                },
                            ],
                        }
                    ],
                },
            },
        }
    }


def _capture(root: Path, row: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    directory = root / "source"
    directory.mkdir()
    urls = {
        "dataset_download": "https://api.neotomadb.org/v2.0/data/downloads/19913",
        "dataset_metadata": "https://api.neotomadb.org/v2.0/data/datasets/19913",
        "neotoma_policy": "https://www.neotomadb.org/data/data-use-and-embargo-policy",
        "epd_policy": "https://epdweblog.org/epd_data_home/epd_policy/",
    }
    metadata = {
        "status": "success",
        "data": [
            {
                "site": {
                    "siteid": 13338,
                    "collectionunitid": 14910,
                    "handle": "ABBO",
                    "datasets": [
                        {
                            "datasetid": 19913,
                            "doi": row["site"]["collectionunit"]["dataset"]["doi"],
                        }
                    ],
                }
            }
        ],
    }
    bodies = {
        "dataset_download": json.dumps({"status": "success", "data": [row]}).encode(),
        "dataset_metadata": json.dumps(metadata).encode(),
        "neotoma_policy": b"Neotoma CC BY 4.0 with attribution",
        "epd_policy": b"European Pollen Database attribution",
    }
    records = []
    for role, body in bodies.items():
        filename = role + ".json"
        (directory / filename).write_bytes(body)
        records.append(
            {
                "role": role,
                "requested_url": urls[role],
                "request_target": urlsplit(urls[role]).path,
                "request_method": "GET",
                "request_headers": [["Accept-Encoding", "identity"]],
                "response_headers": [["Vary", "Origin"], ["Vary", "Accept-Encoding"]],
                "utc_start": "2026-10-26T18:54:13+00:00",
                "utc_end": "2026-10-26T18:54:14+00:00",
                "http_status": 200,
                "body_complete": True,
                "terminal_status": "complete_http_200",
                "body_file": filename,
                "retained_body_bytes": len(body),
                "retained_body_sha256": sha256(body).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "neotoma-single-dataset-http-capture.v1",
        "capture_identity": "neotoma/dataset-19913/current",
        "capture_utc_start": "2026-10-26T18:54:12+00:00",
        "capture_utc_end": "2026-10-26T18:54:15+00:00",
        "status": "complete",
        "historical_capture_replaced": False,
        "rights": {"licence_url": "https://creativecommons.org/licenses/by/4.0/"},
        "records": records,
    }
    return directory, manifest


def _save(directory: Path, manifest: dict[str, Any]) -> str:
    content = json.dumps(manifest).encode()
    (directory / "capture-manifest.json").write_bytes(content)
    return sha256(content).hexdigest()


def _repository(root: Path, row: dict[str, Any]) -> Path:
    repository = root / "repository"
    part = (
        repository / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"
    )
    part.parent.mkdir(parents=True)
    part.write_text(json.dumps({"rows": [row]}))
    return repository


def test_actual_projection_preserves_each_capture_and_reports_changed_source_fields(
    tmp_path: Path,
) -> None:
    old = _row()
    current = deepcopy(old)
    sample = current["site"]["collectionunit"]["dataset"]["samples"][0]
    sample["datum"][0]["value"] = 7
    sample["ages"][0]["age"] = 1210
    sample["unknown_native_field"] = {"reported": False}
    sample["datum"].append(deepcopy(sample["datum"][0]))
    directory, manifest = _capture(tmp_path, current)
    manifest["records"].reverse()
    digest = _save(directory, manifest)
    repository = _repository(tmp_path, old)
    output = repository / "artifacts/comparison"
    report = account.run(repository, directory, digest, output)
    assert report["source_value_equal"] is False
    assert report["changed_paths"] == 4
    captures = report["captures"]
    assert isinstance(captures, dict)
    for capture in captures.values():
        assert capture["native_preservation"]["match"] is True
    assert (
        captures["current"]["native_preservation"]["surfaces"]["observations"][
            "raw_rows"
        ]
        == 3
    )
    assert (
        captures["retained"]["native_preservation"]["surfaces"]["observations"][
            "raw_rows"
        ]
        == 2
    )
    assert all(
        report[key] is False
        for key in (
            "historical_http_custody_recovered",
            "scientific_admission",
            "canonical_data_replaced",
        )
    )
    assert json.loads((output / "changes.json").read_bytes())[0]["path"].startswith(
        "/site/"
    )
    assert json.loads(
        (
            repository
            / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"
        ).read_text()
    )["rows"] == [old]
    assert (
        sha256((directory / "dataset_download.json").read_bytes()).hexdigest()
        in captures["current"]["source_snapshot_id"]
    )


def test_literal_comparison_distinguishes_absence_null_zero_types_and_array_order() -> (
    None
):
    changes = account.source_changes(
        {"missing": None, "zero": 0, "flag": True, "array": [1, 2]},
        {"added": None, "zero": None, "flag": 1, "array": [2, 1]},
    )
    assert {(row["path"], row["kind"]) for row in changes} == {
        ("/missing", "removed"),
        ("/added", "added"),
        ("/zero", "type_changed"),
        ("/flag", "type_changed"),
        ("/array/0", "value_changed"),
        ("/array/1", "value_changed"),
    }
    assert account.source_changes(1, 1.0)[0]["kind"] == "type_changed"


@pytest.mark.parametrize(
    "field,value",
    [
        ("body_complete", False),
        ("http_status", 403),
        ("request_method", "POST"),
        ("request_target", "/wrong"),
        ("requested_url", "https://example.org/19913"),
        ("body_file", "../outside.json"),
        ("utc_start", "2026-10-26T18:54:13"),
        ("utc_end", "2026-10-26T18:54:20+00:00"),
        ("response_headers", [["bad"]]),
        ("retained_body_sha256", "0" * 64),
    ],
)
def test_incomplete_or_mismatched_http_capture_is_refused(
    tmp_path: Path, field: str, value: object
) -> None:
    directory, manifest = _capture(tmp_path, _row())
    manifest["records"][0][field] = value
    digest = _save(directory, manifest)
    with pytest.raises(ValueError, match="Neotoma"):
        account.read_capture(directory, digest)


def test_manifest_body_drift_and_ambiguous_response_populations_are_refused(
    tmp_path: Path,
) -> None:
    directory, manifest = _capture(tmp_path, _row())
    digest = _save(directory, manifest)
    with pytest.raises(ValueError, match="manifest identity"):
        account.read_capture(directory, "0" * 64)
    (directory / "dataset_download.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="response body identity"):
        account.read_capture(directory, digest)
    body = json.dumps({"status": "success", "data": [_row(), _row()]}).encode()
    (directory / "dataset_download.json").write_bytes(body)
    manifest["records"][0].update(
        retained_body_bytes=len(body), retained_body_sha256=sha256(body).hexdigest()
    )
    with pytest.raises(ValueError, match="one successful dataset"):
        account.read_capture(directory, _save(directory, manifest))


def test_duplicate_sample_identity_keeps_a_failed_native_preservation_result() -> None:
    old = _row()
    current = deepcopy(old)
    samples = current["site"]["collectionunit"]["dataset"]["samples"]
    duplicate = deepcopy(samples[0])
    duplicate["depth"] = 999
    samples.append(duplicate)
    report, _ = account.compare_rows(
        old,
        current,
        prior_source="old",
        current_source="current",
        prior_values=old,
        current_values=current,
    )
    captures = report["captures"]
    assert isinstance(captures, dict)
    assert captures["current"]["native_preservation"]["match"] is False
    assert captures["current"]["conflicts"]


def test_raw_body_drift_during_projection_never_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = _row()
    directory, manifest = _capture(tmp_path, row)
    digest = _save(directory, manifest)
    repository = _repository(tmp_path, row)
    original = build_neotoma_relational_snapshot

    def changed(*args: Any, **kwargs: Any) -> dict[str, object]:
        result = original(*args, **kwargs)
        path = directory / "dataset_download.json"
        path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(account, "build_neotoma_relational_snapshot", changed)
    output = repository / "artifacts/refused"
    with pytest.raises(ValueError, match="response body identity"):
        account.run(repository, directory, digest, output)
    assert not output.exists()


def test_cli_preserves_failed_native_comparison_and_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = _row()
    current = deepcopy(old)
    samples = current["site"]["collectionunit"]["dataset"]["samples"]
    duplicate = deepcopy(samples[0])
    duplicate["depth"] = 999
    samples.append(duplicate)
    directory, manifest = _capture(tmp_path, current)
    digest = _save(directory, manifest)
    repository = _repository(tmp_path, old)
    output = repository / "artifacts/refused-native"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "capture_comparison",
            "--repository",
            str(repository),
            "--capture",
            str(directory),
            "--capture-manifest-sha256",
            digest,
            "--output",
            str(output),
        ],
    )
    assert account.main() == 1
    assert json.loads((output / "changes.json").read_bytes())
    report = json.loads((output / "report.json").read_bytes())
    assert report["captures"]["current"]["native_preservation"]["match"] is False


def test_exact_numeric_changes_survive_binary64_equivalence(tmp_path: Path) -> None:
    row = _row()
    directory, manifest = _capture(tmp_path, row)
    body_path = directory / "dataset_download.json"
    current_body = body_path.read_bytes().replace(b'"value": 0', b'"value": 1.0', 1)
    body_path.write_bytes(current_body)
    manifest["records"][0].update(
        retained_body_bytes=len(current_body),
        retained_body_sha256=sha256(current_body).hexdigest(),
    )
    digest = _save(directory, manifest)
    repository = _repository(tmp_path, row)
    part = (
        repository / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"
    )
    part.write_bytes(
        part.read_bytes().replace(b'"value": 0', b'"value": 1.000000000000000001', 1)
    )
    assert float("1.000000000000000001") == float("1.0")
    output = repository / "artifacts/exact-values"
    report = account.run(repository, directory, digest, output)
    assert report["source_value_equal"] is False
    assert report["changed_paths"] == 1
    changes = json.loads((output / "changes.json").read_bytes())
    assert changes[0]["kind"] == "value_changed"
    assert changes[0]["prior"] == {
        "json_numeric_kind": "decimal",
        "exact_value": "1.000000000000000001",
    }
    assert changes[0]["current"] == {
        "json_numeric_kind": "decimal",
        "exact_value": "1.0",
    }
    captures = report["captures"]
    assert isinstance(captures, dict)
    assert all(
        capture["native_preservation"]["match"] is True for capture in captures.values()
    )
    assert account.source_changes(1, Decimal("1.0"))[0]["kind"] == "type_changed"
    assert account.source_changes(Decimal("1.00"), Decimal("1.0")) == []
