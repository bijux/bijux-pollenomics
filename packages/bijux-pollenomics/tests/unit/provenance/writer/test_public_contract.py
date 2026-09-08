"""Compatibility and ownership tests for the release-evidence writer package."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.provenance import writer
from bijux_pollenomics.provenance.writer import (
    main,
    write_release_evidence_manifest,
    write_release_evidence_request,
)


def test_writer_facade_preserves_public_contract() -> None:
    assert writer.__all__ == [
        "main",
        "write_release_evidence_manifest",
        "write_release_evidence_request",
    ]
    assert writer.main is main
    assert writer.write_release_evidence_manifest is write_release_evidence_manifest
    assert writer.write_release_evidence_request is write_release_evidence_request


def test_writer_facade_preserves_private_helper_imports() -> None:
    expected_helpers = {
        "_artifact",
        "_blocker",
        "_bool_field",
        "_canonical_bytes",
        "_existing_repository_path",
        "_fsync_directory",
        "_gate",
        "_int_field",
        "_list_field",
        "_load_json",
        "_mapping",
        "_mapping_field",
        "_open_output_parent",
        "_optional_int_field",
        "_optional_string_field",
        "_parent",
        "_parser",
        "_publish_canonical_document",
        "_read_regular_bytes",
        "_read_regular_bytes_at",
        "_read_repository_json",
        "_reconciliation",
        "_relative_parts",
        "_repository_root",
        "_string_field",
        "_string_value",
        "_validate_written_manifest",
        "_verify_output_parent",
        "_write_request",
    }

    assert all(callable(getattr(writer, name)) for name in expected_helpers)


def test_writer_facade_preserves_legacy_dependency_bindings() -> None:
    expected_bindings = {
        "ArtifactInput",
        "ArtifactReference",
        "ArtifactRole",
        "Blocker",
        "Callable",
        "CountReconciliation",
        "CountStatus",
        "GateResult",
        "GateStatus",
        "Literal",
        "Mapping",
        "Path",
        "PurePosixPath",
        "ReconciliationDimension",
        "ReleaseEvidenceError",
        "Sequence",
        "argparse",
        "build_release_evidence_manifest",
        "cast",
        "json",
        "os",
        "secrets",
        "stat",
        "suppress",
        "sys",
        "validate_release_evidence_manifest",
    }

    assert all(hasattr(writer, name) for name in expected_bindings)


def test_writer_implementation_is_intent_owned_and_bounded() -> None:
    package = Path(writer.__file__).parent
    modules = sorted(package.glob("*.py"))

    assert not package.with_suffix(".py").exists()
    assert {path.stem for path in modules} == {
        "__init__",
        "arguments",
        "cli",
        "codec",
        "publication",
        "reconciliation",
        "repository",
        "service",
        "translation",
    }
    assert (
        max(len(path.read_text(encoding="utf-8").splitlines()) for path in modules)
        <= 200
    )
