"""Tests for policy-bound hosted scientific-evidence creation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from bijux_pollenomics.analysis.propagation.outputs import (
    PropagationMaterializationResult,
    PropagationOutputRefusalError,
)
from bijux_pollenomics.evidence.classification.audit_outputs import (
    ClassificationAuditMaterializationResult,
    ClassificationAuditRefusalError,
)
from bijux_pollenomics_dev.ci import scientific_evidence
from bijux_pollenomics_dev.ci.scientific_evidence import (
    ScientificEvidenceMaterializationError,
    materialize_scientific_evidence,
)

from .fixtures import repository_fixture


def _install_successful_producers(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(
        scientific_evidence,
        "_classification_snapshot",
        lambda *_: {
            "source_family": "neotoma",
            "source_snapshot_id": "sha256:source",
            "build_id": "sha256:build",
            "sites": [],
            "variables": [],
            "observations": [],
        },
    )
    monkeypatch.setattr(
        scientific_evidence,
        "build_neotoma_classification_accounting",
        lambda snapshot: {"snapshot": snapshot},
    )
    invocation_counts = {"classification": 0, "propagation": 0}

    def classification(*args: object, **kwargs: Any) -> object:
        del args
        calls.append("classification")
        invocation_counts["classification"] += 1
        paths = kwargs["paths"]
        assert paths.output_root.parent.is_dir()
        return ClassificationAuditMaterializationResult(
            output_root=paths.output_root,
            disposition=(
                "created" if invocation_counts["classification"] == 1 else "unchanged"
            ),
            manifest_sha256="c" * 64,
            file_count=10,
            concept_count=3,
            observation_count=7,
            accepted_mapping_count=0,
            release_status="refused",
        )

    def propagation(events: object, **kwargs: Any) -> object:
        calls.append("propagation")
        assert events == ()
        assert kwargs["output_root"].parent.is_dir()
        invocation_counts["propagation"] += 1
        return PropagationMaterializationResult(
            output_root=kwargs["output_root"],
            disposition=(
                "created" if invocation_counts["propagation"] == 1 else "unchanged"
            ),
            manifest_sha256="d" * 64,
            file_count=8,
            eligible_event_count=0,
            excluded_non_pollen_event_count=0,
            primary_directed_candidate_count=0,
        )

    monkeypatch.setattr(
        scientific_evidence, "materialize_classification_audit", classification
    )
    monkeypatch.setattr(
        scientific_evidence, "materialize_propagation_outputs", propagation
    )
    return calls


def test_classification_precedes_zero_accepted_propagation_and_repeats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = repository_fixture(tmp_path, monkeypatch)
    calls = _install_successful_producers(root, monkeypatch)

    created = materialize_scientific_evidence(root.absolute())
    unchanged = materialize_scientific_evidence(root.absolute())

    assert calls == ["classification", "propagation"] * 2
    assert created.classification.disposition == "created"
    assert created.propagation.disposition == "created"
    assert unchanged.classification.disposition == "unchanged"
    assert unchanged.propagation.disposition == "unchanged"
    assert created.classification.accepted_mapping_count == 0
    assert created.propagation.eligible_event_count == 0


def test_policy_path_must_bind_each_bundle_to_its_producer_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, policy = repository_fixture(tmp_path, monkeypatch)
    artifacts = cast(list[dict[str, Any]], policy["required_artifacts"])
    propagation = next(
        entry for entry in artifacts if entry["identity"] == "propagation"
    )
    propagation["path"] = (
        "artifacts/execution-control/propagation/unbound/manifest.json"
    )
    (root / "configs/release_evidence_policy.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )

    with pytest.raises(ScientificEvidenceMaterializationError) as refusal:
        materialize_scientific_evidence(root.absolute())

    assert refusal.value.reason_code == "invalid_evidence_identity"


def test_local_contract_digest_change_is_refused_before_source_loading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = repository_fixture(tmp_path, monkeypatch)
    (root / "configs/scientific-contracts/propagation-model.v1.yaml").write_text(
        "changed: true\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        scientific_evidence,
        "_classification_snapshot",
        lambda *_: pytest.fail("source loading must follow contract validation"),
    )

    with pytest.raises(ScientificEvidenceMaterializationError) as refusal:
        materialize_scientific_evidence(root.absolute())

    assert refusal.value.reason_code == "invalid_scientific_contract"


def test_relational_validation_failure_prevents_both_publications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = repository_fixture(tmp_path, monkeypatch)
    called: list[str] = []

    def invalid_manifest(_root: Path) -> dict[str, object]:
        raise ValueError("digest mismatch")

    monkeypatch.setattr(
        scientific_evidence,
        "read_validated_neotoma_relational_manifest",
        invalid_manifest,
    )
    monkeypatch.setattr(
        scientific_evidence,
        "materialize_classification_audit",
        lambda *args, **kwargs: called.append("classification"),
    )
    monkeypatch.setattr(
        scientific_evidence,
        "materialize_propagation_outputs",
        lambda *args, **kwargs: called.append("propagation"),
    )

    with pytest.raises(ScientificEvidenceMaterializationError) as refusal:
        materialize_scientific_evidence(root.absolute())

    assert refusal.value.reason_code == "invalid_relational_manifest"
    assert called == []


def test_relational_part_digest_is_rechecked_after_manifest_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = repository_fixture(tmp_path, monkeypatch)
    part_path = root / "data/neotoma/relational/surfaces/sites/part-00001.json"
    part_path.parent.mkdir(parents=True)
    part_path.write_text('{"rows": []}\n', encoding="utf-8")
    manifest: dict[str, object] = {
        "relational_snapshot_schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:source",
        "build_id": "sha256:build",
        "surfaces": {
            "sites": {
                "row_count": 0,
                "parts": [
                    {
                        "path": "surfaces/sites/part-00001.json",
                        "row_count": 0,
                        "sha256": "0" * 64,
                    }
                ],
            }
        },
    }
    monkeypatch.setattr(
        scientific_evidence,
        "read_validated_neotoma_relational_manifest",
        lambda _: manifest,
    )

    with pytest.raises(ScientificEvidenceMaterializationError) as refusal:
        materialize_scientific_evidence(root.absolute())

    assert refusal.value.reason_code == "invalid_relational_manifest"
    assert "changed after validation" in str(refusal.value)


def test_nonzero_accepted_universe_requires_an_explicit_event_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = repository_fixture(tmp_path, monkeypatch)
    current_authority = cast(
        Any, vars(scientific_evidence)["_CLASSIFICATION_AUTHORITY"]
    )
    authority = replace(current_authority, accepted_mapping_count=1)
    monkeypatch.setattr(scientific_evidence, "_CLASSIFICATION_AUTHORITY", authority)
    _install_successful_producers(root, monkeypatch)

    def accepted(*args: object, **kwargs: Any) -> object:
        del args
        paths = kwargs["paths"]
        return ClassificationAuditMaterializationResult(
            output_root=paths.output_root,
            disposition="created",
            manifest_sha256="c" * 64,
            file_count=10,
            concept_count=1,
            observation_count=1,
            accepted_mapping_count=1,
            release_status="review_required",
        )

    propagated: list[bool] = []
    monkeypatch.setattr(
        scientific_evidence, "materialize_classification_audit", accepted
    )
    monkeypatch.setattr(
        scientific_evidence,
        "materialize_propagation_outputs",
        lambda *args, **kwargs: propagated.append(True),
    )

    with pytest.raises(ScientificEvidenceMaterializationError) as refusal:
        materialize_scientific_evidence(root.absolute())

    assert (
        refusal.value.reason_code == "accepted_classification_events_not_materialized"
    )
    assert propagated == []


@pytest.mark.parametrize(
    "refusal_type",
    [ClassificationAuditRefusalError, PropagationOutputRefusalError],
)
def test_cli_reports_product_publisher_refusals_without_a_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    refusal_type: type[ValueError],
) -> None:
    def refuse(
        _root: Path,
    ) -> scientific_evidence.ScientificEvidenceMaterializationResult:
        raise refusal_type("governed_refusal", "publication refused")

    monkeypatch.setattr(scientific_evidence, "materialize_scientific_evidence", refuse)

    exit_code = scientific_evidence.main(
        ["--repository-root", str(tmp_path.absolute())]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == "governed_refusal: publication refused\n"
