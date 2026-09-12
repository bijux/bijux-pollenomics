"""A complete real-file fixture produces a stable, source-bound refusal ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.sead import audit_sead_lra_source

from .support import admitted_fixture


def test_public_audit_reconciles_every_fixture_row_and_repeats(tmp_path: Path) -> None:
    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    manifests = []
    for name in ("first", "second"):
        report = audit_sead_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=expected,
            output_directory=tmp_path / name,
        )
        manifest_bytes = (report.output_directory / "manifest.json").read_bytes()
        assert hashlib.sha256(manifest_bytes).hexdigest() == report.manifest_sha256
        manifest = json.loads(manifest_bytes)
        assert manifest["available_observations"] == 4
        assert manifest["available_analysis_entities"] == 1
        assert manifest["entity_linked_physical_samples"] == 1
        assert manifest["source_physical_samples"] == 1
        assert manifest["physical_samples_without_analysis_entity"] == 0
        assert len(manifest["source_table_row_counts"]) == 61
        assert manifest["lra_accepted_samples"] == 0
        assert manifest["country_accounting"]["UNASSIGNED"]["observations"] == 0
        assert manifest["country_accounting"]["SE"]["observations"] == 4
        for member in manifest["artifacts"]:
            data = (report.output_directory / member["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == member["sha256"]
        manifests.append(manifest_bytes)
    assert manifests[0] == manifests[1]
    with pytest.raises(FileExistsError):
        audit_sead_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=expected,
            output_directory=tmp_path / "first",
        )


def test_concurrent_directory_is_preserved_by_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra.materialization.sead import workflow
    from bijux_pollenomics.core.owned_tree import publish_new_output_tree

    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    output = tmp_path / "output"

    def competing_writer(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        (final_output_root / "other-owner.txt").write_text("preserve")
        publish_new_output_tree(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(workflow, "publish_new_output_tree", competing_writer)
    with pytest.raises(FileExistsError):
        audit_sead_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=expected,
            output_directory=output,
        )
    assert (output / "other-owner.txt").read_text() == "preserve"
    assert not (output / "manifest.json").exists()


def test_mutated_source_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra.materialization.sead.reading import SeadEvidence

    raw, normalized, expected = admitted_fixture(tmp_path / "fixture")
    original = SeadEvidence.assert_unchanged
    calls = 0

    def mutate_at_final_check(self: SeadEvidence) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            member = normalized / "source_native_observations.json"
            member.write_bytes(member.read_bytes() + b" ")
        original(self)

    monkeypatch.setattr(SeadEvidence, "assert_unchanged", mutate_at_final_check)
    with pytest.raises(ValueError, match="changed"):
        audit_sead_lra_source(
            raw_root=raw,
            normalized_root=normalized,
            expected_identity=expected,
            output_directory=tmp_path / "output",
        )
    assert not (tmp_path / "output").exists()


def test_unlinked_raw_sample_has_an_explicit_denominator_without_inferred_country(
    tmp_path: Path,
) -> None:
    raw, normalized, expected = admitted_fixture(
        tmp_path / "fixture", unlinked_sample=True
    )
    report = audit_sead_lra_source(
        raw_root=raw,
        normalized_root=normalized,
        expected_identity=expected,
        output_directory=tmp_path / "audit",
    )
    manifest = json.loads((report.output_directory / "manifest.json").read_bytes())
    assert report.available_samples == 1
    assert manifest["entity_linked_physical_samples"] == 1
    assert manifest["source_physical_samples"] == 2
    assert manifest["physical_samples_without_analysis_entity"] == 1
    assert (
        sum(
            row["entity_linked_physical_samples"]
            for row in manifest["country_accounting"].values()
        )
        == 1
    )
    assert (
        manifest["country_accounting"]["UNASSIGNED"]["entity_linked_physical_samples"]
        == 0
    )
