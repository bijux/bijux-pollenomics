"""Expose the maintained lookup and finite contrast through the real module CLI."""

from hashlib import sha256
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from .test_archive import Retained, api, encoded, publish, source
from .test_contrast import frontier, target


def cli() -> Any:
    """Require an ordinary source-owned command interface."""
    name = "bijux_pollenomics.collection.sources.neotoma.ancillary_store.taxonomy_reference.command_line"
    assert importlib.util.find_spec(name) is not None, "Dated reference CLI is missing"
    return importlib.import_module(name).main


def test_lookup_cli_preserves_literal_nulls_and_source_positions(
    retained: Retained, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, directory, _, pin = publish(retained, tmp_path)
    status = cli()(
        [
            "lookup",
            "--archive",
            str(directory),
            "--manifest-sha256",
            pin,
            "--taxon-id",
            "1",
        ]
    )
    assert status == 0
    value = json.loads(capsys.readouterr().out)
    assert value["records"][0]["native_id"] == 1
    assert value["reference_manifest_sha256"] == pin
    assert value["records"][0]["metadata"]["citation"] is None
    assert [row["assertion_position"] for row in value["records"][0]["synonyms"]] == [
        0,
        1,
    ]
    assert value["current_roles_revalidated"] is False
    assert value["database_dates_are_sample_ages"] is False


def test_contrast_cli_uses_owned_report_publication(
    retained: Retained, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, directory, _, pin = publish(retained, tmp_path)
    chain, chain_pin = frontier(
        tmp_path, [target("publication", 99), target("taxon", 999)]
    )
    output = tmp_path / "comparison"
    status = cli()(
        [
            "contrast-frontier",
            "--archive",
            str(directory),
            "--manifest-sha256",
            pin,
            "--chain",
            str(chain),
            "--chain-manifest-sha256",
            chain_pin,
            "--output",
            str(output),
        ]
    )
    assert status == 0
    value = json.loads((output / "frontier-contrast.json").read_bytes())
    assert value["summary"]["frozen_frontier_rows"] == 2
    assert value["summary"]["unmatched_targets"] == 1
    assert value["GET_authorized"] is False
    assert (
        json.loads(capsys.readouterr().out)["status"]
        == "published_recorded_reference_contrast"
    )


def test_retain_cli_uses_independently_pinned_local_source_plan(
    retained: Retained, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provenance = source(api(), retained)
    value = {
        "revision": provenance.revision,
        "files": {
            name: {"path": str(pin.path), "bytes": pin.bytes, "sha256": pin.sha256}
            for name, pin in provenance.files.items()
        },
        "git_metadata": {
            name: {"path": str(pin.path), "bytes": pin.bytes, "sha256": pin.sha256}
            for name, pin in provenance.git_metadata.items()
        },
        "transport": {
            name: {"path": str(pin.path), "bytes": pin.bytes, "sha256": pin.sha256}
            for name, pin in provenance.transport.items()
        },
        "intake_intervals": dict(provenance.intake_intervals),
        "attribution": provenance.attribution,
    }
    raw = encoded(value)
    plan = tmp_path / "source-plan.json"
    plan.write_bytes(raw)
    output = tmp_path / "cli-archive"
    assert (
        cli()(
            [
                "retain",
                "--source-plan",
                str(plan),
                "--source-plan-sha256",
                sha256(raw).hexdigest(),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert (
        result["manifest_sha256"]
        == sha256((output / "manifest.json").read_bytes()).hexdigest()
    )
    assert result["native_detail_captures_added"] == 0
    assert (output / "originals/taxa_snapshot.json").read_bytes() == (
        retained[0] / "taxa_snapshot.json"
    ).read_bytes()
