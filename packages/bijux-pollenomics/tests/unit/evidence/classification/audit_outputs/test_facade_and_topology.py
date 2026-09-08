"""Compatibility and ownership boundaries for classification-audit outputs."""

from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.evidence.classification import audit_outputs

_PUBLIC_API = (
    "ClassificationAuditMaterializationResult",
    "ClassificationAuditOutputPaths",
    "ClassificationAuditRefusalError",
    "materialize_classification_audit",
)
_LEGACY_PRIVATE_API = frozenset(
    {
        "_ACCEPTED_STATUSES",
        "_COUNTRY_PARTITION",
        "_MANIFEST_NAME",
        "_MAPPING_STATUSES",
        "_OUTPUT_NAMES",
        "_REVIEW_STATUSES",
        "_SHA256_PATTERN",
        "_ZERO_ACCEPTED_REASON_CODES",
        "_build_manifest",
        "_build_payloads",
        "_canonical_json_bytes",
        "_country_partitions",
        "_existing_bundle_is_identical",
        "_mapping_sequence",
        "_nonempty",
        "_observation_country_counts",
        "_payload_record_count",
        "_publish_atomically",
        "_queue_payload",
        "_queue_row",
        "_refuse",
        "_required_digest",
        "_required_text",
        "_sequence_values",
        "_sha256",
        "_validate_accounting_reconciliation",
        "_validate_output_paths",
        "_validated_accounting_rows",
    }
)
_OWNED_MODULES = frozenset(
    {
        "accounting.py",
        "constants.py",
        "manifest.py",
        "models.py",
        "partitions.py",
        "payloads.py",
        "publication.py",
        "queues.py",
        "values.py",
        "workflow.py",
    }
)


def test_legacy_facade_preserves_public_and_private_imports() -> None:
    assert tuple(audit_outputs.__all__) == _PUBLIC_API
    assert frozenset(vars(audit_outputs)) >= _LEGACY_PRIVATE_API

    signature = inspect.signature(audit_outputs.materialize_classification_audit)
    assert tuple(signature.parameters) == (
        "accounting",
        "paths",
        "allowed_output_parent",
        "classification_contract_version",
        "classification_contract_digest",
        "classification_producer_id",
        "classification_producer_version",
        "classification_producer_digest",
    )
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in tuple(signature.parameters)[1:]
    )


def test_audit_output_modules_have_bounded_intent_ownership() -> None:
    package_root = Path(audit_outputs.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
        if path.name != "__init__.py"
    }

    assert frozenset(modules) == _OWNED_MODULES
    assert len(modules) <= 10
    assert max(modules.values()) <= 200
