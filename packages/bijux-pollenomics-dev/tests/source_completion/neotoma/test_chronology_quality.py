"""Source support reports bind real receipts and refuse publication drift."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics_dev.source_completion.neotoma.chronology_quality"
    )


def write_json(path: Path, value: object) -> bytes:
    content = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def repository(root: Path) -> tuple[Path, Path]:
    """Make a valid raw archive and its actual maintained relational projection."""
    raw = root / "data/neotoma/raw/neotoma_pollen_dataset_downloads"
    normalized = root / "data/neotoma/relational"
    source: dict[str, Any] = {
        "site": {
            "siteid": 1,
            "sitename": "Synthetic retained site",
            "geography": '{"type":"Point","coordinates":[15,60]}',
            "collectionunit": {
                "collectionunitid": 1,
                "chronologies": [],
                "defaultchronology": None,
                "dataset": {
                    "datasetid": 1,
                    "samples": [
                        {
                            "sampleid": 100,
                            "depth": 10,
                            "ages": [
                                {
                                    "chronologyid": 999,
                                    "agetype": "Calendar years BP",
                                    "age": 100,
                                },
                                {
                                    "chronologyid": 998,
                                    "agetype": "Radiocarbon years BP",
                                    "age": 110,
                                },
                            ],
                            "datum": [],
                        },
                        {
                            "sampleid": 101,
                            "depth": 20,
                            "depthunits": "mm",
                            "ages": [],
                            "datum": [],
                        },
                    ],
                },
            },
            "dataset": {"datasetid": 1},
        }
    }
    identity = {
        "generated_on": "2026-04-01",
        "source": "Neotoma",
        "endpoint_template": "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
        "datasettype": "pollen",
        "row_count": 1,
        "downloaded_dataset_count": 1,
        "downloaded_dataset_ids": [1],
    }
    parts = []
    for index in range(1, 10):
        row = deepcopy(source)
        site = row["site"]
        site["siteid"] = index
        site["dataset"]["datasetid"] = index
        unit = site["collectionunit"]
        unit["collectionunitid"] = index
        unit["dataset"]["datasetid"] = index
        for offset, sample in enumerate(unit["dataset"]["samples"]):
            sample["sampleid"] = index * 100 + offset
        filename = f"part-{index:03d}.json"
        content = write_json(
            raw / filename,
            {
                **identity,
                "downloaded_dataset_ids": [index],
                "part_number": index,
                "part_count": 9,
                "rows": [row],
            },
        )
        parts.append(
            {
                "filename": filename,
                "part_number": index,
                "row_count": 1,
                "downloaded_dataset_count": 1,
                "downloaded_dataset_ids": [index],
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    write_json(
        raw / "manifest.json",
        {
            **identity,
            "row_count": 9,
            "downloaded_dataset_count": 9,
            "downloaded_dataset_ids": list(range(1, 10)),
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
            "requested_dataset_count": 9,
            "requested_dataset_ids": list(range(1, 10)),
            "rows_per_part": 1,
            "part_count": 9,
            "parts": parts,
        },
    )
    rows, snapshot_id = load_validated_neotoma_raw_archive(raw)
    snapshot = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=snapshot_id,
        build_id="synthetic-build",
        country_by_site_id=dict.fromkeys(range(1, 10), "SE"),
    )
    materialize_neotoma_relational_snapshot(normalized, snapshot, rows_per_part=1)
    (root / "artifacts").mkdir()
    return raw, normalized


def test_report_keeps_all_profiles_claims_and_unaged_flags_reproducibly(
    tmp_path: Path,
) -> None:
    raw, normalized = repository(tmp_path)
    oldscreen = (
        tmp_path / "docs/report/source-relations/neotoma/pollen-screen/report.json"
    )
    write_json(oldscreen, {"immutable_historical_screen": True})
    original = oldscreen.read_bytes()
    first, second = tmp_path / "artifacts/one.json", tmp_path / "artifacts/two.json"
    report = owner().run(tmp_path, first)
    assert owner().run(tmp_path, second) == report
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_bytes()) == report
    quality = report["source_chronology_quality"]
    assert len(quality["profiles"]) == 18
    assert len(quality["claim_diagnostics"]) == 18
    assert quality["sample_flags"]["neotoma:sample:101"] == [
        "explicit_depth_unit_contradiction",
        "sample_has_no_source_age_claim",
    ]
    assert quality["source_denominators"] == {
        "samples": 18,
        "age_claims": 18,
        "chronologies": 0,
        "chronology_controls": 0,
        "source_conflicts": 0,
    }
    assert report["source_identity"]["build_id"] == "synthetic-build"
    assert (
        report["source_identity"]["source_snapshot_id"]
        == json.loads((normalized / "manifest.json").read_bytes())["source_snapshot_id"]
    )
    assert {row["authority"] for row in report["source_input_records"]} == {
        "raw",
        "normalized",
    }
    for row in report["source_input_records"]:
        base = raw if row["authority"] == "raw" else normalized
        assert (
            hashlib.sha256((base / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    assert report["source_profile_eligibility_changed"] is False
    assert report["source_identity"]["materialization_sha256"]
    assert (
        report["implementation_identity"]["producer_sha256"]
        == hashlib.sha256(Path(str(owner().__file__)).read_bytes()).hexdigest()
    )
    from bijux_pollenomics.collection.sources.neotoma.chronology import (
        quality as host_quality,
    )

    host_identity = report["implementation_identity"]["host"]
    assert host_identity["scope"] == "bijux_pollenomics_python_package"
    quality_path = Path(host_quality.__file__)
    quality_pin = next(
        record
        for record in host_identity["files"]
        if record["path"].endswith("collection/sources/neotoma/chronology/quality.py")
    )
    assert (
        quality_pin["sha256"] == hashlib.sha256(quality_path.read_bytes()).hexdigest()
    )
    assert oldscreen.read_bytes() == original
    assert not list(first.parent.glob("*.stage"))


def test_valid_foreign_raw_snapshot_does_not_establish_normalized_identity(
    tmp_path: Path,
) -> None:
    raw, _ = repository(tmp_path)
    part = json.loads((raw / "part-001.json").read_bytes())
    part["rows"][0]["site"]["sitename"] = "Foreign valid snapshot"
    changed = write_json(raw / "part-001.json", part)
    manifest = json.loads((raw / "manifest.json").read_bytes())
    manifest["parts"][0]["sha256"] = hashlib.sha256(changed).hexdigest()
    write_json(raw / "manifest.json", manifest)
    output = tmp_path / "artifacts/report.json"
    with pytest.raises(ValueError, match="does not bind the raw snapshot"):
        owner().run(tmp_path, output)
    assert not output.exists() and not output.with_suffix(".json.stage").exists()


@pytest.mark.parametrize(
    "change",
    [
        "raw",
        "normalized",
        "implementation",
        "staged_report",
        "staged_bytes",
        "destination",
    ],
)
def test_postread_changes_cannot_be_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    raw, normalized = repository(tmp_path)
    module = owner()
    output = tmp_path / "artifacts/report.json"
    copied_code = tmp_path / "artifacts/producer.py"
    copied_code.write_bytes(Path(str(module.__file__)).read_bytes())
    monkeypatch.setattr(module, "__file__", str(copied_code))
    original_read = Path.read_bytes

    def read_after_change(path: Path) -> bytes:
        if path == output.with_suffix(".json.stage"):
            if change == "destination":
                output.write_bytes(b"existing result\n")
            elif change == "staged_report":
                path.write_bytes(b'{"wrong_report":true}\n')
            elif change == "staged_bytes":
                path.write_bytes(original_read(path) + b"\n")
            else:
                target = {
                    "raw": raw / "part-001.json",
                    "normalized": normalized / "surfaces/samples/part-00001.json",
                    "implementation": copied_code,
                }[change]
                target.write_bytes(target.read_bytes() + b"\n")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", read_after_change)
    with pytest.raises((ValueError, ReportRebuildError, FileExistsError)):
        module.run(tmp_path, output)
    assert output.with_suffix(".json.stage").is_file()
    if change == "destination":
        assert output.read_bytes() == b"existing result\n"
    else:
        assert not output.exists()


@pytest.mark.parametrize(
    "destination", ["existing", "outside", "symlink", "stage_existing"]
)
def test_output_refusals_preserve_existing_files(
    tmp_path: Path, destination: str
) -> None:
    repository(tmp_path)
    output = tmp_path / "artifacts/report.json"
    if destination == "outside":
        output = tmp_path / "report.json"
    elif destination == "existing":
        output.write_bytes(b"preserved")
    elif destination == "stage_existing":
        output.with_suffix(".json.stage").write_bytes(b"preserved")
    else:
        target = tmp_path / "artifacts/target.json"
        target.write_bytes(b"preserved")
        output.symlink_to(target)
    before = {
        p: p.read_bytes() for p in (tmp_path / "artifacts").iterdir() if p.is_file()
    }
    with pytest.raises(ReportRebuildError):
        owner().run(tmp_path, output)
    assert all(path.read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize(
    "change", ["stage_bytes", "stage_inode", "destination_inode", "destination_exists"]
)
def test_late_publication_changes_refuse_without_removing_foreign_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    repository(tmp_path)
    module = owner()
    output = tmp_path / "artifacts/report.json"
    stage = output.with_suffix(".json.stage")
    foreign = b'{"foreign_stage":true}\n'
    actual_link = module.os.link

    def substitute_then_link(source: Path, target: Path) -> None:
        if change == "destination_exists":
            target.write_bytes(foreign)
        elif change in {"stage_bytes", "stage_inode"}:
            if change == "stage_inode":
                source.unlink()
            source.write_bytes(foreign)
        actual_link(source, target)
        if change == "destination_inode":
            target.unlink()
            target.write_bytes(foreign)

    monkeypatch.setattr(module.os, "link", substitute_then_link)
    with pytest.raises((ValueError, FileExistsError)):
        module.run(tmp_path, output)
    assert output.read_bytes() == foreign
    assert stage.is_file()
    if change == "stage_inode":
        assert stage.read_bytes() == foreign


def test_success_does_not_remove_a_replaced_stage_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository(tmp_path)
    module = owner()
    output = tmp_path / "artifacts/report.json"
    stage = output.with_suffix(".json.stage")
    foreign = b"another writer's stage\n"
    actual_link = module.os.link

    def link_then_replace_stage(source: Path, target: Path) -> None:
        actual_link(source, target)
        source.unlink()
        source.write_bytes(foreign)

    monkeypatch.setattr(module.os, "link", link_then_replace_stage)
    report = module.run(tmp_path, output)
    assert json.loads(output.read_bytes()) == report
    assert stage.read_bytes() == foreign


def test_destination_replaced_after_readback_is_not_reported_as_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository(tmp_path)
    output = tmp_path / "artifacts/report.json"
    actual_open = Path.open
    foreign = b'{"another_writer":true}\n'

    @contextmanager
    def open_then_replace(path: Path, *args: Any, **kwargs: Any) -> Iterator[Any]:
        with actual_open(path, *args, **kwargs) as stream:
            yield stream
        if path == output and (args == ("rb",) or kwargs.get("mode") == "rb"):
            path.unlink()
            path.write_bytes(foreign)

    monkeypatch.setattr(Path, "open", open_then_replace)
    with pytest.raises(ValueError):
        owner().run(tmp_path, output)
    assert output.read_bytes() == foreign


def test_cli_writes_one_full_report(tmp_path: Path) -> None:
    repository(tmp_path)
    output = tmp_path / "artifacts/report.json"
    assert owner().main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    assert (
        len(
            json.loads(output.read_bytes())["source_chronology_quality"]["sample_flags"]
        )
        == 18
    )
