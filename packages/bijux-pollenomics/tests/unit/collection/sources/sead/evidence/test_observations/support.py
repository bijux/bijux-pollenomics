from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SeadScopedAcquisitionResult,
    acquire_full_evidence_sead_relations,
)

_SITE_FIELDS = (
    "site_id",
    "site_name",
    "national_site_identifier",
    "latitude_dd",
    "longitude_dd",
    "altitude",
    "site_description",
    "site_uuid",
)


class _FullEvidencePostgrestFixture:
    def __init__(
        self, *, corrupt_table: str | None = None, null_dataset: bool = False
    ) -> None:
        self.corrupt_table = corrupt_table
        self.null_dataset = null_dataset
        self.calls: list[tuple[str, list[tuple[str, str]]]] = []

    def __call__(
        self,
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        del timeout
        table = endpoint.rsplit("/", 1)[-1]
        self.calls.append((table, list(params)))
        projection = next(value for key, value in params if key == "select")
        fields = projection.split(",")
        row: dict[str, object] = {field: None for field in fields}
        for field in fields:
            if field.endswith("_id"):
                row[field] = 1
            elif field.startswith("is_") or field == "boolean_value":
                row[field] = False
            elif field in {"abundance", "value"}:
                row[field] = 0
        if table == "tbl_sites":
            row.update(
                {
                    "site_id": 1,
                    "site_name": "native site",
                    "latitude_dd": 56.0,
                    "longitude_dd": 13.0,
                    "site_uuid": "sead-site-uuid-1",
                }
            )
        elif table == "tbl_analysis_values":
            row["analysis_value"] = "0"
        elif table == "tbl_analysis_entities" and self.null_dataset:
            row["dataset_id"] = None

        dependency_filter = next(
            ((field, value) for field, value in params if value.startswith("in.(")),
            None,
        )
        if dependency_filter is not None and table == self.corrupt_table:
            row[dependency_filter[0]] = 2

        start, end = (int(value) for value in headers["Range"].split("-", 1))
        return [row][start : end + 1]


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 5, 12, 0, tzinfo=UTC)


def _acquire(
    output_root: Path, fetcher: _FullEvidencePostgrestFixture
) -> SeadScopedAcquisitionResult:
    return acquire_full_evidence_sead_relations(
        output_root,
        bbox=(5.0, 50.0, 30.0, 70.0),
        governed_country_by_site_id={1: "SE"},
        country_assignment_id="sha256:" + "3" * 64,
        scope_id="sha256:" + "1" * 64,
        run_id="full-evidence-run-001",
        parent_run_id="parent-fixture-001",
        build_id="sha256:" + "2" * 64,
        fetch_json_fn=fetcher,
        clock=_fixed_clock,
        sleep_fn=lambda _seconds: None,
    )


def _full_admission_inputs(
    snapshot: Path, root: Path
) -> tuple[Path, Path, SeadAdmissionExpectedIdentity]:
    decisions = (root / "country-decisions.json").resolve()
    decisions.write_text(
        json.dumps(
            {
                "decisions": [
                    {
                        "site_id": 1,
                        "governed_country_code": "SE",
                        "decision": {"decision_method": "strict_boundary_containment"},
                    }
                ]
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    decision_sha256 = hashlib.sha256(decisions.read_bytes()).hexdigest()
    parent = (root / "parent-admission.json").resolve()
    parent_payload = {
        "schema_version": "sead-acquisition-admission.v1",
        "source_family": "sead",
        "run_id": "parent-fixture-001",
        "copied_files": [{"path": "country-decisions.json", "sha256": decision_sha256}],
    }
    parent.write_text(
        json.dumps(parent_payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return (
        decisions,
        parent,
        SeadAdmissionExpectedIdentity(
            scope_id="sha256:" + "1" * 64,
            run_id="full-evidence-run-001",
            parent_run_id="parent-fixture-001",
            build_id="sha256:" + "2" * 64,
            country_authority_id="sha256:" + "3" * 64,
            country_authority_artifact_digest="sha256:" + "4" * 64,
            country_authority_root=root.resolve(),
            bbox_payload_sha256="5" * 64,
            acquisition_manifest_sha256=hashlib.sha256(
                (snapshot / "manifest.json").read_bytes()
            ).hexdigest(),
            country_decisions_sha256=decision_sha256,
            parent_admission_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),
        ),
    )


def _refresh_capture_manifest(snapshot: Path) -> None:
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    for path in sorted(snapshot.rglob("*")):
        if path.is_file() and path != manifest_path:
            content = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(snapshot).as_posix(),
                    "byte_count": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    manifest["files"] = files
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
