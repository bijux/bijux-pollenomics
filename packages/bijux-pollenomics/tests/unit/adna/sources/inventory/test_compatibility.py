"""Source-inventory compatibility and ownership tests."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.sources import inventory
from bijux_pollenomics.adna.sources.inventory import (
    blocker_review,
    materialization,
    model,
    project_evidence,
    reference_reconciliation,
    rendering,
    supplements,
)


def test_facade_preserves_the_source_inventory_contract() -> None:
    assert inventory.__all__ == [
        "build_cross_project_source_intake_dossier",
        "build_project_source_evidence_matrix",
        "build_reference_stash_doi_integrity_audit",
        "build_reference_stash_reconciliation",
        "build_supplement_acquisition_checklist",
        "build_supplement_file_family_audit",
        "build_supplement_recovery_audit",
        "build_source_blocker_review",
        "build_tracked_project_scope_audit",
        "materialize_source_inventory",
    ]
    assert inventory.SOURCE_INVENTORY_SCHEMA_VERSION == "adna-source-inventory.v1"
    assert (
        inventory.materialize_source_inventory
        is materialization.materialize_source_inventory
    )
    assert (
        inventory.build_source_blocker_review
        is blocker_review.build_source_blocker_review
    )
    assert inventory._count_by is model._count_by
    assert (
        inventory.build_project_source_evidence_matrix
        is project_evidence.build_project_source_evidence_matrix
    )
    assert (
        inventory.build_reference_stash_reconciliation
        is reference_reconciliation.build_reference_stash_reconciliation
    )
    assert (
        inventory.render_supplement_recovery_audit_markdown
        is rendering.render_supplement_recovery_audit_markdown
    )
    assert (
        inventory.build_supplement_recovery_audit
        is supplements.build_supplement_recovery_audit
    )


def test_inventory_modules_remain_bounded_by_durable_responsibility() -> None:
    package_root = Path(inventory.__file__).parent
    module_names = {
        path.stem for path in package_root.glob("*.py") if path.name != "__init__.py"
    }
    assert module_names == {
        "blocker_review",
        "materialization",
        "model",
        "project_evidence",
        "reference_reconciliation",
        "rendering",
        "supplements",
    }
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )
