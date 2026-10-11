"""Small real-file acquisitions using the existing SEAD source fixture owners."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.models import (
    SourceRow,
    canonical_bytes,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    materialize_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    acquire_full_evidence_sead_relations,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    write_sead_source_native_evidence_bundle,
)
from tests.unit.collection.sources.sead.acquisition.test_admission.fixtures.builder import (
    _expected_identity,
    _write_fixture,
)
from tests.unit.collection.sources.sead.acquisition.test_admission.fixtures.receipts import (
    _query_receipt,
)
from tests.unit.collection.sources.sead.evidence.test_observations.support import (
    _fixed_clock,
    _FullEvidencePostgrestFixture,
)


def source_row(payload: dict[str, Any], surface: str = "fixture") -> SourceRow:
    return SourceRow(surface, "fixture.json", 0, canonical_bytes(payload))


def admitted_fixture(
    root: Path, *, unlinked_sample: bool = False
) -> tuple[Path, Path, SeadAdmissionExpectedIdentity]:
    root.mkdir(parents=True, exist_ok=True)
    old_snapshot, decisions_path = _write_fixture(root / "country")
    old_identity = _expected_identity(old_snapshot, decisions_path)
    result = acquire_full_evidence_sead_relations(
        root / "capture",
        bbox=(4.0, 54.0, 35.0, 72.0),
        governed_country_by_site_id={1: "SE"},
        country_assignment_id=old_identity.country_authority_id,
        scope_id=old_identity.scope_id,
        run_id="full-evidence-audit-fixture",
        parent_run_id=old_identity.run_id,
        build_id=old_identity.build_id,
        fetch_json_fn=_UnlinkedPhysicalSampleFixture()
        if unlinked_sample
        else _FullEvidencePostgrestFixture(),
        clock=_fixed_clock,
        sleep_fn=lambda _: None,
    )
    capture = result.manifest_path.parent.resolve()
    decisions = json.loads(decisions_path.read_bytes())
    site_rows = json.loads((capture / "payloads/tbl_sites.json").read_bytes())["rows"]
    decisions["decisions"][0]["site_uuid"] = site_rows[0]["site_uuid"]
    previous = decisions["preflight_receipt"]
    decisions["preflight_receipt"] = _query_receipt(
        "tbl_sites",
        rows=site_rows,
        spatial_scope=previous["spatial_scope"],
        parameters=previous["parameters"],
        max_pages=100,
    )
    decisions_path.write_bytes(canonical_bytes(decisions))
    parent = root / "parent-admission.json"
    parent.write_bytes(
        canonical_bytes(
            {
                "schema_version": "sead-acquisition-admission.v1",
                "source_family": "sead",
                "run_id": old_identity.run_id,
                "copied_files": [
                    {
                        "path": "country-decisions.json",
                        "sha256": hashlib.sha256(
                            decisions_path.read_bytes()
                        ).hexdigest(),
                    }
                ],
            }
        )
    )
    expected = replace(
        old_identity,
        run_id="full-evidence-audit-fixture",
        parent_run_id=old_identity.run_id,
        acquisition_manifest_sha256=hashlib.sha256(
            result.manifest_path.read_bytes()
        ).hexdigest(),
        country_decisions_sha256=hashlib.sha256(
            decisions_path.read_bytes()
        ).hexdigest(),
        bbox_payload_sha256=decisions["preflight_receipt"]["content_sha256"],
        parent_admission_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),
    )
    admitted = materialize_sead_full_evidence_admission(
        capture,
        country_decisions_path=decisions_path,
        parent_admission_path=parent,
        output_root=(root / "raw").resolve(),
        expected_identity=expected,
    )
    normalized = (root / "normalized").resolve()
    write_sead_source_native_evidence_bundle(
        admitted.output_root, normalized, expected_identity=expected
    )
    return admitted.output_root, normalized, expected


class _UnlinkedPhysicalSampleFixture(_FullEvidencePostgrestFixture):
    def __call__(
        self,
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        rows = super().__call__(
            endpoint, params=params, headers=headers, timeout=timeout
        )
        if (
            endpoint.endswith("/tbl_physical_samples")
            and isinstance(rows, list)
            and rows
        ):
            return [rows[0], {**rows[0], "physical_sample_id": 2}]
        return rows
