"""Release-evidence product policy tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
    validate_release_evidence_manifest,
)
from bijux_pollenomics.provenance import request as request_module
from bijux_pollenomics.provenance.release_evidence import artifacts as release_artifacts
from bijux_pollenomics.provenance.release_evidence import (
    assessment as release_assessment,
)
from bijux_pollenomics.provenance.release_evidence import embedded as release_embedded
from bijux_pollenomics.provenance.release_evidence import models as release_models
from bijux_pollenomics.provenance.release_evidence import policy as release_policy
from bijux_pollenomics.provenance.release_evidence import service as release_service

from tests.support.repository import REPOSITORY_ROOT

from .support import (
    _arguments,
    _canonical_json,
)


def test_product_request_policy_has_exact_inventory_and_reconciliation_counts() -> None:
    root = REPOSITORY_ROOT
    policy = release_policy._load_release_evidence_policy(root)

    rows = request_module._reconciliations(root, policy)
    by_identity = {row.identity: row for row in rows}

    assert len(policy.required_artifacts) == 27
    assert len(policy.required_gate_ids) == 5
    assert len(policy.required_reconciliations) == 28
    assert len(rows) == 390
    assert len({(row.source, row.entity) for row in rows}) == 28
    assert {
        status: sum(row.count_status == status for row in rows)
        for status in ("reported", "unavailable", "refused")
    } == {"reported": 334, "unavailable": 42, "refused": 14}
    release_assessment._validate_reconciliations(rows, policy)
    classification_metrics = {
        requirement.entity: requirement.derivation_metric
        for requirement in policy.required_reconciliations
        if requirement.source == "classification"
    }
    assert classification_metrics == {
        "ambiguous": "ambiguous_concepts",
        "concepts": "distinct_concepts",
        "mapped": "mapped_concepts",
        "unmapped": "unmapped_concepts",
    }

    sead = by_identity["sead.sites.source"]
    assert (
        sead.candidate_count,
        sead.eligible_count,
        sead.accepted_count,
        sead.unresolved_count,
        sead.excluded_count,
    ) == (2195, 2069, 2069, 103, 23)
    assert by_identity["sead.sites.country.unassigned"].unresolved_count == 103
    assert by_identity["sead.sites.country.outside"].excluded_count == 23
    chronology_claims = by_identity["sead.chronology_claims.source"]
    assert (
        chronology_claims.candidate_count,
        chronology_claims.eligible_count,
        chronology_claims.accepted_count,
        chronology_claims.unresolved_count,
        chronology_claims.excluded_count,
        chronology_claims.refused_count,
    ) == (25_109, 24_468, 14_264, 641, 0, 10_204)

    observations = by_identity["neotoma.observations.country.unassigned"]
    assert observations.count_status == "reported"
    assert (observations.candidate_count, observations.unresolved_count) == (9700, 9700)
    outside = by_identity["neotoma.observations.country.outside"]
    assert outside.count_status == "reported"
    assert (outside.candidate_count, outside.excluded_count) == (0, 0)

    concepts = by_identity["classification.concepts.source"]
    unmapped = by_identity["classification.unmapped.source"]
    assert (
        concepts.candidate_count,
        concepts.accepted_count,
        concepts.unresolved_count,
        concepts.excluded_count,
    ) == (2555, 0, 2481, 74)
    candidate_count = cast(int, concepts.candidate_count)
    assert candidate_count > 1351  # Country memberships, not global concepts.
    assert (unmapped.candidate_count, unmapped.unresolved_count) == (2481, 2481)
    assert by_identity["raa.records.source"].count_status == "refused"
    assert by_identity["raa.records.source"].candidate_count is None
    assert by_identity["propagation.evaluated_pairs.source"].candidate_count == 0


def test_product_request_policy_has_coherent_full_artifact_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = REPOSITORY_ROOT
    policy = release_policy._load_release_evidence_policy(root)
    artifacts, digests = request_module._artifact_inputs(root, policy)
    records = [
        release_artifacts._artifact_record(root, artifact) for artifact in artifacts
    ]
    dependency_lock = next(
        digests[item.identity]
        for item in policy.required_artifacts
        if item.role == "dependency_lock"
    )
    validate_schema = release_embedded._validate_embedded_schema_identity

    def allow_pre_refresh_gate_schema(
        repository_root: Path,
        artifact: ArtifactInput,
        requirement: release_models._RequiredArtifact,
    ) -> None:
        if artifact.role != "validation_result":
            validate_schema(repository_root, artifact, requirement)

    monkeypatch.setattr(
        release_artifacts,
        "_validate_embedded_schema_identity",
        allow_pre_refresh_gate_schema,
    )

    release_artifacts._validate_artifact_graph(
        root,
        artifacts,
        records,
        dependency_lock,
        policy,
    )


def test_product_manifest_validation_rejects_caller_supplied_reconciliations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = _arguments(tmp_path)
    manifest = release_service.build_release_evidence_manifest(
        tmp_path,
        code_commit=cast(str, arguments["code_commit"]),
        dirty=cast(bool, arguments["dirty"]),
        dependency_lock_digest=cast(str, arguments["dependency_lock_digest"]),
        artifacts=cast(list[ArtifactInput], arguments["artifacts"]),
        gates=cast(list[GateResult], arguments["gates"]),
        reconciliations=cast(list[CountReconciliation], arguments["reconciliations"]),
        blockers=(),
    )
    fixture_policy = release_policy._load_release_evidence_policy(tmp_path)
    product_policy = replace(fixture_policy, mode="product")
    governed = tuple(cast(list[CountReconciliation], arguments["reconciliations"]))
    forged = cast(list[dict[str, object]], manifest["reconciliations"])
    forged[0]["candidate_count"] = cast(int, forged[0]["candidate_count"]) + 1
    forged[0]["eligible_count"] = cast(int, forged[0]["eligible_count"]) + 1
    forged[0]["accepted_count"] = cast(int, forged[0]["accepted_count"]) + 1
    monkeypatch.setattr(
        release_service,
        "_load_release_evidence_policy",
        lambda _root: product_policy,
    )
    monkeypatch.setattr(
        request_module, "_reconciliations", lambda _root, _policy: governed
    )

    with pytest.raises(ReleaseEvidenceError, match="governed derivation"):
        validate_release_evidence_manifest(tmp_path, manifest)


def test_country_adapter_rejects_dimension_substitution(tmp_path: Path) -> None:
    root = REPOSITORY_ROOT
    policy = release_policy._load_release_evidence_policy(root)
    requirement = next(
        item
        for item in policy.required_reconciliations
        if (item.source, item.entity) == ("sead", "sites")
    )
    cells = [
        {
            "source_family": "sead",
            "country_dimension": "source_reported",
            "resolution": "source",
            "country_code": country,
            "counts": {"sites": 0},
            "reason_codes": [],
        }
        for country in release_models._COUNTRIES
    ]
    ledger = tmp_path / "data/country_dimension_coverage.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(_canonical_json({"cells": cells}) + b"\n")

    assert request_module._governed_country_values(tmp_path, requirement) is None
