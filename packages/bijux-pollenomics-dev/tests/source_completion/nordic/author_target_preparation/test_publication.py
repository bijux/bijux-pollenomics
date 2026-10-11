"""Preserve exact products, confined publication and occupied outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    require_mapping,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.nordic import (
    author_target_preparation as account,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy.author_mass import (
    DESCRIPTOR,
)

from .fixtures import Packet, _run, _unpublished
from .fixtures import packet as packet


def test_exact_retained_matrices_publish_with_source_separation_and_two_qualifications(
    packet: Packet,
) -> None:
    before = {name: path.read_bytes() for name, path in packet.qualified.inputs.items()}
    assert _run(packet) == packet.manifest
    assert packet.calls == ["qualify", "prepare", "qualify"]
    for relative, data in packet.products.items():
        assert (packet.output / relative).read_bytes() == data
    assert len(packet.products) == 9
    assert packet.manifest["target_outcomes_in_prediction_inputs"] is False
    assert {
        name: path.read_bytes() for name, path in packet.qualified.inputs.items()
    } == before
    assert {p.name for p in packet.output.parent.iterdir()} == {"result"}


@pytest.mark.parametrize(
    "placement", ["existing", "escape", "traversal", "symlink-leaf", "symlink-parent"]
)
def test_unconfined_or_occupied_output_refuses_before_source(
    packet: Packet, placement: str
) -> None:
    original = packet.output
    if placement == "existing":
        original.mkdir()
        (original / "user.txt").write_bytes(b"preserve")
    elif placement == "escape":
        packet.output = packet.repository.parent / "escaped"
    elif placement == "traversal":
        packet.output = original.parent / ".." / "artifacts/result"
    elif placement == "symlink-leaf":
        original.symlink_to(packet.root, target_is_directory=True)
    else:
        parent = original.parent / "linked"
        parent.symlink_to(packet.root, target_is_directory=True)
        packet.output = parent / "result"
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet.calls == []
    if placement == "existing":
        assert (original / "user.txt").read_bytes() == b"preserve"


@pytest.mark.parametrize(
    "failure",
    [
        "schema",
        "axis",
        "axis-order",
        "lookup",
        "bool-age",
        "source",
        "separation",
        "upstream",
        "hash-coverage",
        "hash-drift",
        "extra-field",
    ],
)
def test_changed_source_receipt_refuses_publication(
    packet: Packet, failure: str
) -> None:
    if failure == "schema":
        packet.manifest["schema_version"] = "wrong"
    elif failure in {"axis", "axis-order"}:
        value = packet.manifest["axis"]
        assert isinstance(value, list)
        value.pop() if failure == "axis" else value.reverse()
    elif failure == "lookup":
        packet.manifest["lookup_rows"] = 1
    elif failure == "bool-age":
        packet.manifest["age_bin_width_bp"] = False
    elif failure == "source":
        packet.manifest["source_snapshot_id"] = "wrong"
    elif failure == "separation":
        packet.manifest["target_outcomes_in_prediction_inputs"] = True
    elif failure == "upstream":
        packet.manifest["author_mass_report_sha256"] = "0" * 64
    elif failure in {"hash-coverage", "hash-drift"}:
        hashes = require_mapping(
            packet.manifest["produced_file_sha256"], "product fixture hashes"
        )
        hashes.pop(
            "inputs/training-DK.json.gz"
        ) if failure == "hash-coverage" else hashes.update(
            {"inputs/training-DK.json.gz": "0" * 64}
        )
    else:
        packet.manifest["extra"] = 1
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize(
    "failure",
    [
        "exception",
        "extra",
        "missing",
        "product-drift",
        "manifest-drift",
        "linked-file",
        "linked-directory",
        "appeared",
    ],
)
def test_bad_producer_outputs_never_overwrite_or_leave_partial_products(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def mutate(repo: Path, directory: Path, output: Path) -> None:
        packet.prepare(repo, directory, output)
        if failure == "exception":
            raise ValueError("original preparation refused")
        if failure == "extra":
            (output / "extra.json").write_bytes(b"{}")
        elif failure == "missing":
            (output / "inputs/metadata-DK.json.gz").unlink()
        elif failure == "product-drift":
            (output / "inputs/metadata-DK.json.gz").write_bytes(b"different")
        elif failure == "manifest-drift":
            (output / "input-manifest.json").write_text(
                json.dumps(packet.manifest), encoding="utf-8"
            )
        elif failure == "linked-file":
            path = output / "inputs/metadata-DK.json.gz"
            path.unlink()
            path.symlink_to(packet.qualified.directory / LOOKUP)
        elif failure == "linked-directory":
            for path in (output / "sealed-outcomes").iterdir():
                path.unlink()
            (output / "sealed-outcomes").rmdir()
            (output / "sealed-outcomes").symlink_to(
                packet.root, target_is_directory=True
            )
        else:
            packet.output.mkdir()
            (packet.output / "user.txt").write_bytes(b"preserve")

    monkeypatch.setattr(account, "prepare", mutate)
    with pytest.raises((ReportRebuildError, ValueError)):
        _run(packet)
    if failure == "appeared":
        assert (packet.output / "user.txt").read_bytes() == b"preserve"
        assert {p.name for p in packet.output.parent.iterdir()} == {"result"}
    else:
        _unpublished(packet)


def test_cli_keeps_prepare_stage_and_explicit_qualified_source(packet: Packet) -> None:
    assert (
        account.main(
            [
                "--repository",
                str(packet.repository),
                "--source-root",
                str(packet.root),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--output",
                str(packet.output),
            ]
        )
        == 0
    )
    assert packet.calls == ["qualify", "prepare", "qualify"]
