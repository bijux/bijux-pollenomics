"""Normalization readers select only declared, independently bound metadata."""

from hashlib import sha256
import json

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    source_inputs,
)


def metadata(tmp_path, monkeypatch):
    reports = {}
    for role in source_inputs.normalization.ROLES:
        raw = json.dumps({"generated": role}).encode()
        path = (
            tmp_path / source_inputs.normalization.PUBLIC_PREFIX / role / "report.json"
        )
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        reports[role] = (sha256(raw).hexdigest(), len(raw))
    monkeypatch.setattr(source_inputs, "REPORT_PINS", reports)
    root = tmp_path / source_inputs.legacyvegetation.DIRECTORY
    root.mkdir(parents=True)
    declarations = [
        {"path": name, "sha256": sha256(name.encode()).hexdigest(), "bytes": len(name)}
        for name in source_inputs.legacyvegetation.TABLES
    ]
    raw = json.dumps({"reference_tables": declarations}).encode()
    (root / "source.json").write_bytes(raw)
    monkeypatch.setattr(
        source_inputs.legacyvegetation, "SOURCE_SHA256", sha256(raw).hexdigest()
    )
    return {
        "source_pins": [
            {
                "path": "source.json",
                "sha256": sha256(raw).hexdigest(),
                "bytes": len(raw),
            },
            *declarations,
        ]
    }


def test_metadata_reader_keeps_unselected_siblings_opaque(tmp_path, monkeypatch):
    reference = metadata(tmp_path, monkeypatch)
    (
        tmp_path / source_inputs.legacyvegetation.DIRECTORY / "unselected.body"
    ).write_bytes(b"not admitted metadata")
    buffers, scope = source_inputs.read_normalization_context(tmp_path, reference)
    assert set(buffers) == set(source_inputs.normalization.ROLES) | {"reference-source"}
    assert len(scope["normalization_evidence"]) == len(scope["metadata"]) == 3


@pytest.mark.parametrize(
    "damage", ["reference_csv_pin", "report_bytes", "source_bytes", "alias"]
)
def test_metadata_reader_refuses_changed_source_bindings(tmp_path, monkeypatch, damage):
    reference = metadata(tmp_path, monkeypatch)
    role = source_inputs.normalization.ROLES[0]
    report = tmp_path / source_inputs.normalization.PUBLIC_PREFIX / role / "report.json"
    if damage == "reference_csv_pin":
        reference["source_pins"][1]["sha256"] = "0" * 64
    elif damage == "report_bytes":
        report.write_bytes(b"changed source")
    elif damage == "source_bytes":
        (
            tmp_path / source_inputs.legacyvegetation.DIRECTORY / "source.json"
        ).write_bytes(b"{}")
    else:
        report.rename(report.with_name("moved.json"))
        report.symlink_to("moved.json")
    with pytest.raises((ValueError, OSError)):
        source_inputs.read_normalization_context(tmp_path, reference)
