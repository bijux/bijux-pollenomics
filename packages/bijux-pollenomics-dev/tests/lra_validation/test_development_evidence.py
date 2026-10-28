"""Retained source refusals and immutable development execution stay visible."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.lra_validation import development_evidence

REPOSITORY = Path(__file__).resolve().parents[4]


def test_preserves_development_only_source_refusals_and_native_audits() -> None:
    report = development_evidence.build_development_evidence(REPOSITORY)
    assert len(report["fresh_audit_attempts"]) == 36
    assert report["fresh_terminal_counts"] == {"completed": 36}
    assert len(report["failed_runtime_attempts"]) == 36
    assert all(
        row["terminal"]["status"] == "failed"
        for row in report["failed_runtime_attempts"]
    )
    assert report["all_fresh_execution_counts"] == {
        "attempted": 72,
        "completed_audit": 36,
        "failed_before_audit": 36,
    }
    assert len(report["original_attempts"]) == 2208
    assert report["original_status_counts"] == {"scored": 2100, "refused": 108}
    assert report["original_refusal_reason_counts"] == {
        "fitted_model_requires_two_training_sites": 90,
        "no_training_site_same_bin": 18,
    }
    assert report["development_cohort"]["outcome_access_status"] == "previously_exposed"
    assert (
        report["claims"]["historical_search_prospectively_frozen_by_this_packet"]
        is False
    )
    assert report["claims"]["fresh_model_fit_or_parameter_sweep"] is False
    assert report["claims"]["untouched_test_or_empirical_vegetation_accuracy"] is False
    names = report["target_support"]["support"]["taxon_names"]
    assert len(names) == 31 and names == sorted(set(names))


@pytest.mark.parametrize("tamper", ["contents", "symlink"])
def test_refuses_modified_or_redirected_execution_record(
    tmp_path: Path, tamper: str
) -> None:
    packet = tmp_path / development_evidence.PACKET
    shutil.copytree(REPOSITORY / development_evidence.PACKET, packet)
    manifest = json.loads((packet / "manifest.json").read_text())
    identity = manifest["fresh_attempt_ids"][0]
    terminal = packet / "ledger" / identity / "result.json"
    if tamper == "contents":
        terminal.write_text('{"status":"completed"}\n')
    else:
        replacement = tmp_path / "replacement.json"
        shutil.copyfile(terminal, replacement)
        terminal.unlink()
        terminal.symlink_to(replacement)
    with pytest.raises(ValueError, match="development_evidence_"):
        development_evidence.build_development_evidence(tmp_path)


def test_refuses_replaced_packet_manifest(tmp_path: Path) -> None:
    packet = tmp_path / development_evidence.PACKET
    packet.mkdir(parents=True)
    (packet / "manifest.json").write_text('{"files":{}}\n')
    with pytest.raises(ValueError, match="development_evidence_manifest_changed"):
        development_evidence.build_development_evidence(tmp_path)
