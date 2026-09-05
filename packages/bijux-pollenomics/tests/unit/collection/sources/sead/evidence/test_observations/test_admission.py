from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    materialize_sead_full_evidence_admission,
    validate_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    service as admission_service,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

from .support import (
    _FullEvidencePostgrestFixture,
    _acquire,
    _full_admission_inputs,
    _refresh_capture_manifest,
)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("scope_id", "nordic-full-evidence-v1"),
        ("build_id", "9ffb8b28"),
    ),
)
def test_full_evidence_admission_refuses_noncryptographic_identity(
    tmp_path: Path, field: str, value: str
) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "manifest.json").write_text("{}", encoding="utf-8")
    decisions = tmp_path / "country-decisions.json"
    decisions.write_text("{}", encoding="utf-8")
    parent = tmp_path / "parent-admission.json"
    parent.write_text("{}", encoding="utf-8")
    values = {
        "scope_id": "sha256:" + "1" * 64,
        "build_id": "sha256:" + "2" * 64,
    }
    values[field] = value
    expected = SeadAdmissionExpectedIdentity(
        scope_id=values["scope_id"],
        run_id="full-evidence-run",
        parent_run_id="parent-run",
        build_id=values["build_id"],
        country_authority_id="sha256:" + "3" * 64,
        country_authority_artifact_digest="sha256:" + "4" * 64,
        country_authority_root=tmp_path,
        bbox_payload_sha256="5" * 64,
        acquisition_manifest_sha256=hashlib.sha256(b"{}").hexdigest(),
        country_decisions_sha256=hashlib.sha256(b"{}").hexdigest(),
        parent_admission_sha256=hashlib.sha256(b"{}").hexdigest(),
    )

    with pytest.raises(ValueError, match=f"expected {field}"):
        validate_sead_full_evidence_admission(
            snapshot.resolve(),
            country_decisions_path=decisions.resolve(),
            parent_admission_path=parent.resolve(),
            expected_identity=expected,
        )


def test_full_evidence_admission_validates_exact_profile_and_parent(
    tmp_path: Path,
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)

    with (
        patch.object(
            admission_service,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_service,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admission = validate_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            expected_identity=expected,
        )

    scope = admission["declared_scope"]
    assert isinstance(scope, dict)
    assert scope["table_count"] == 61
    assert scope["join_count"] == 86
    assert scope["tables"] == sorted(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    assert (
        admission["parent_admission_sha256"]
        == hashlib.sha256(parent.read_bytes()).hexdigest()
    )


def test_full_evidence_admission_allows_sibling_parent_evidence(
    tmp_path: Path,
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent_admission, expected = _full_admission_inputs(snapshot, tmp_path)
    acquisition_parent = (tmp_path / "admitted").resolve()
    parent_root = acquisition_parent / expected.parent_run_id
    parent_root.mkdir(parents=True)
    governed_decisions = parent_root / "country-decisions.json"
    governed_parent_admission = parent_root / "admission.json"
    governed_decisions.write_bytes(decisions.read_bytes())
    governed_parent_admission.write_bytes(parent_admission.read_bytes())

    with (
        patch.object(
            admission_service,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_service,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=governed_decisions,
            parent_admission_path=governed_parent_admission,
            output_root=acquisition_parent,
            expected_identity=expected,
        )

    assert admitted.output_root == acquisition_parent / expected.run_id
    assert governed_decisions.is_file()
    assert governed_parent_admission.is_file()


def test_full_evidence_admission_recomputes_all_join_ledgers(tmp_path: Path) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    joins_path = snapshot / "reconciliation" / "joins.json"
    joins = json.loads(joins_path.read_text(encoding="utf-8"))
    joins["edges"][-1]["matched_child_count"] = 999
    joins_path.write_text(
        json.dumps(joins, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    _refresh_capture_manifest(snapshot)
    expected = SeadAdmissionExpectedIdentity(
        **{
            **expected.__dict__,
            "acquisition_manifest_sha256": hashlib.sha256(
                (snapshot / "manifest.json").read_bytes()
            ).hexdigest(),
        }
    )

    with (
        patch.object(
            admission_service,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_service,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
        pytest.raises(ValueError, match="independently recomputed ledger"),
    ):
        validate_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            expected_identity=expected,
        )
