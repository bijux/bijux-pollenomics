"""Synthetic contracts for joining independently prepared native and live-R cases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import file_inventory
from bijux_pollenomics_dev.ci.lra_reference.native_parity import verify_native_parity

from .support import LOCK, SHA, bundle_fixture


def _synthetic_pair(root: Path) -> tuple[Path, Path]:
    live = root / "live"
    bundle_fixture(live)
    manifest_path = live / "oracle/case_manifest.json"
    rows = json.loads(manifest_path.read_text())
    for index, row in enumerate(rows):
        row["input_sha256"] = hashlib.sha256(f"input-{index}".encode()).hexdigest()
        row["python_expected_sha256"] = hashlib.sha256(
            f"expected-{index}".encode()
        ).hexdigest()
    manifest_bytes = (json.dumps(rows) + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)
    certificate_path = live / "certificate.json"
    certificate = json.loads(certificate_path.read_text())
    certificate["files"] = file_inventory(live)
    certificate["files"].pop("certificate.json", None)
    certificate_path.write_text(json.dumps(certificate))

    native = root / "native"
    native.mkdir()
    (native / "case_manifest.json").write_bytes(manifest_bytes)
    live_report = json.loads((live / "oracle/report.json").read_text())
    (native / "report.json").write_text(
        json.dumps(
            {
                "status": "prepared_not_executed",
                "live_R_executed": False,
                "prepared_cases": 43,
                "passed_cases": 0,
                "source_archive_sha256": live_report["source_archive_sha256"],
            }
        )
    )
    return native, live


def test_parity_receipt_binds_cases_and_complete_r_bundle(tmp_path: Path) -> None:
    native, live = _synthetic_pair(tmp_path)
    output = tmp_path / "receipt.json"
    receipt = verify_native_parity(
        native=native, live=live, lock=LOCK, target_sha=SHA, output=output
    )
    assert receipt["case_count"] == 43
    assert (
        receipt["case_manifest_sha256"]
        == hashlib.sha256((native / "case_manifest.json").read_bytes()).hexdigest()
    )
    assert receipt["live_R_executed"] is True
    assert json.loads(output.read_text()) == receipt


@pytest.mark.parametrize("mutation", ["missing_digest", "different_input", "missing_r"])
def test_parity_refuses_incomplete_or_changed_evidence(
    tmp_path: Path, mutation: str
) -> None:
    native, live = _synthetic_pair(tmp_path)
    if mutation in {"missing_digest", "different_input"}:
        path = native / "case_manifest.json"
        rows = json.loads(path.read_text())
        if mutation == "missing_digest":
            del rows[0]["input_sha256"]
        else:
            rows[0]["input_sha256"] = "0" * 64
        path.write_text(json.dumps(rows))
    else:
        (live / "oracle/R_case_status.csv").unlink()
    with pytest.raises(ReferenceRefusal):
        verify_native_parity(
            native=native,
            live=live,
            lock=LOCK,
            target_sha=SHA,
            output=tmp_path / "receipt.json",
        )
    assert not (tmp_path / "receipt.json").exists()
