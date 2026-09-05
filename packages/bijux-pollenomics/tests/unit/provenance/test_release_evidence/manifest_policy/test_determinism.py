"""Manifest determinism and local-attestation decision tests."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.provenance import GateResult, validate_release_evidence_manifest

from ..support import _artifacts, _build, _reconciliations


def test_manifest_is_deterministic_for_shuffled_inputs(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path, gate_id="alpha", gate_ids=("alpha", "zeta"))
    alpha_validation = next(
        artifact for artifact in artifacts if artifact.identity == "validation"
    )
    zeta_validation = next(
        artifact for artifact in artifacts if artifact.identity == "zeta-validation"
    )
    gates = [
        GateResult("zeta", "PASS", True, zeta_validation.output_digest),
        GateResult("alpha", "PASS", True, alpha_validation.output_digest),
    ]
    reconciliations = _reconciliations()

    first = _build(
        tmp_path, artifacts=artifacts, gates=gates, reconciliations=reconciliations
    )
    second = _build(
        tmp_path,
        artifacts=list(reversed(artifacts)),
        gates=list(reversed(gates)),
        reconciliations=list(reversed(reconciliations)),
    )

    assert first == second
    assert first["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "required_gate_not_independently_attested:alpha",
            "required_gate_not_independently_attested:zeta",
        ],
    }
    validate_release_evidence_manifest(tmp_path, first)


def test_coherent_local_pass_is_diagnostic_but_never_release_ready(
    tmp_path: Path,
) -> None:
    manifest = _build(tmp_path)

    assert manifest["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "required_gate_not_independently_attested:quality",
        ],
    }
