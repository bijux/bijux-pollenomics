"""Recorded-gate compatibility-facade tests."""

from __future__ import annotations

from bijux_pollenomics.provenance import gates


def test_facade_preserves_public_and_legacy_private_seams() -> None:
    assert gates.__all__ == [
        "RecordedGateSpecification",
        "build_product_gate_specification",
        "run_recorded_gate",
    ]
    assert {
        "_GATE_FIXED_INPUTS",
        "_GATE_GLOBS",
        "_GATE_TESTS",
        "_GATE_TRUST_INPUTS",
        "_IDENTITY_PATTERN",
        "_LOCAL_ATTESTATION",
        "_PRODUCER_ID",
        "_PRODUCER_MODULE",
        "_PRODUCER_VERSION",
        "_artifact_member",
        "_atomic_replace",
        "_canonical_bytes",
        "_digest_json",
        "_exact_argv",
        "_exact_environment",
        "_fsync_directory",
        "_input_records",
        "_output_record",
        "_prepare_artifacts_directory",
        "_producer_record",
        "_read_executing_source_bytes",
        "_relative_parts",
        "_repository_root",
        "_runtime_identity",
        "_temporary_path",
        "_validate_gate_id",
        "_validate_passing_junit",
    } <= set(vars(gates))


def test_provenance_gate_selects_component_tests() -> None:
    assert "provenance/gates" in gates._GATE_TESTS["provenance"]
