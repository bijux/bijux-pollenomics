from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.data_downloader.sources.sead.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.data_downloader.sources.sead.acquisition_admission import (
    SeadAdmissionExpectedIdentity,
    materialize_sead_full_evidence_admission,
    validate_sead_full_evidence_admission,
)
from bijux_pollenomics.data_downloader.sources.sead import (
    acquisition_admission as admission_module,
)
from bijux_pollenomics.data_downloader.sources.sead import (
    evidence_bundle as evidence_module,
)
from bijux_pollenomics.data_downloader.sources.sead.evidence_bundle import (
    build_sead_source_native_evidence_bundle,
    validate_sead_source_native_evidence_materialization,
    write_sead_source_native_evidence_bundle,
)
from bijux_pollenomics.data_downloader.sources.sead.scoped_acquisition import (
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
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


def test_full_evidence_plan_is_distinct_and_dependency_ordered() -> None:
    assert len(SEAD_LINKED_SOURCE_TABLES) == 19
    assert set(SEAD_LINKED_SOURCE_TABLES) < set(SEAD_FULL_EVIDENCE_SOURCE_TABLES)

    plan_by_table = {plan.table: plan for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS}
    assert len(plan_by_table) == len(SEAD_FULL_EVIDENCE_TABLE_PLANS)
    assert ("tbl_sites", *(plan.table for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS)) == (
        SEAD_FULL_EVIDENCE_SOURCE_TABLES
    )

    available = {"tbl_sites"}
    projected_by_table = {"tbl_sites": set(_SITE_FIELDS)}
    for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS:
        fields = set(plan.projection.split(","))
        assert plan.primary_key in fields
        assert plan.filter_field in fields
        for dependency in plan.dependencies:
            assert dependency.table in available
            assert dependency.field in projected_by_table[dependency.table]
        available.add(plan.table)
        projected_by_table[plan.table] = fields

    for join in SEAD_FULL_EVIDENCE_JOIN_PLANS:
        assert join.parent_key in projected_by_table[join.parent_table]
        assert join.child_key in projected_by_table[join.child_table]
        assert join.child_foreign_key in projected_by_table[join.child_table]

    declared_joins = {
        (
            join.parent_table,
            join.child_table,
            join.parent_key,
            join.child_foreign_key,
        )
        for join in SEAD_FULL_EVIDENCE_JOIN_PLANS
    }
    assert len({join.edge for join in SEAD_FULL_EVIDENCE_JOIN_PLANS}) == len(
        SEAD_FULL_EVIDENCE_JOIN_PLANS
    )
    for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS:
        for dependency in plan.dependencies:
            if plan.filter_field == plan.primary_key:
                expected_join = (
                    plan.table,
                    dependency.table,
                    plan.primary_key,
                    dependency.field,
                )
            else:
                expected_join = (
                    dependency.table,
                    plan.table,
                    dependency.field,
                    plan.filter_field,
                )
            assert expected_join in declared_joins


def test_full_evidence_acquisition_is_bounded_and_preserves_native_values(
    tmp_path: Path,
) -> None:
    fetcher = _FullEvidencePostgrestFixture()
    result = _acquire(tmp_path, fetcher)

    assert tuple(item.table for item in result.acquisitions) == (
        SEAD_FULL_EVIDENCE_SOURCE_TABLES
    )
    assert len(result.join_reconciliations) == len(SEAD_FULL_EVIDENCE_JOIN_PLANS)
    assert all(item["status"] == "complete" for item in result.join_reconciliations)

    acquisitions = {item.table: item for item in result.acquisitions}
    assert acquisitions["tbl_abundances"].rows[0]["abundance"] == 0
    assert acquisitions["tbl_analysis_values"].rows[0]["analysis_value"] == "0"
    assert acquisitions["tbl_analysis_values"].rows[0]["boolean_value"] is False
    assert all(
        item.receipt["tool_version"] == FULL_EVIDENCE_ORCHESTRATOR_VERSION
        for item in result.acquisitions
    )
    for item in result.acquisitions:
        spatial_scope = item.receipt["spatial_scope"]
        assert isinstance(spatial_scope, dict)
        assert spatial_scope["relation_scope"] == "full_evidence_relations"

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["required_tables"] == sorted(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    assert manifest["status"] == "complete"

    calls_by_table = {table: params for table, params in fetcher.calls}
    assert set(calls_by_table) == set(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    for table, params in fetcher.calls:
        if table != "tbl_sites":
            identity_filters = [
                (field, value) for field, value in params if value.startswith("in.(")
            ]
            assert len(identity_filters) == 1
            assert identity_filters[0][1] == "in.(1)"


def test_full_evidence_acquisition_refuses_a_source_ignored_filter(
    tmp_path: Path,
) -> None:
    fetcher = _FullEvidencePostgrestFixture(corrupt_table="tbl_abundances")

    with pytest.raises(
        ValueError,
        match=(
            "SEAD source ignored dependency filter for tbl_abundances: "
            "analysis_entity_id=2"
        ),
    ):
        _acquire(tmp_path, fetcher)


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


def test_source_native_evidence_preserves_every_row_and_is_fixed_point(
    tmp_path: Path,
) -> None:
    result = _acquire(
        tmp_path / "capture", _FullEvidencePostgrestFixture(null_dataset=True)
    )
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    with (
        patch.object(
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=(tmp_path / "admitted").resolve(),
            expected_identity=expected,
        )
        acquisition = admitted.output_root
        bundle = build_sead_source_native_evidence_bundle(
            acquisition, expected_identity=expected
        )
        observations = bundle["source_native_observations.json"]
        events = bundle["evidence_events.json"]
        assert observations["observation_count"] == 4
        assert observations["observation_table_counts"] == {
            "tbl_abundances": 1,
            "tbl_analysis_taxon_counts": 1,
            "tbl_analysis_values": 1,
            "tbl_measured_values": 1,
        }
        rows = observations["observations"]
        assert isinstance(rows, list)
        assert [row["source_value"] for row in rows] == [0, 0, "0", None]
        taxon_count = rows[1]
        assert taxon_count["taxon_relation_id"] == "sead-taxon:1"
        assert events["observation_denominator"] == 4
        assert events["eligible_event_count"] == 0
        assert events["refused_event_count"] == 4
        relation_index = bundle["observation_relation_index.json"]
        entity_relations = relation_index["entity_relations"]
        assert isinstance(entity_relations, list)
        assert entity_relations[0]["dataset_id"] is None
        assert relation_index["dimension_relation_count"] == 5
        assert relation_index["dimension_semantic_count"] == 1
        dimension_relations = relation_index["dimension_relations"]
        assert isinstance(dimension_relations, list)
        assert {row["source_table"] for row in dimension_relations} == {
            "tbl_analysis_value_dimensions",
            "tbl_measured_value_dimensions",
            "tbl_analysis_entity_dimensions",
            "tbl_sample_dimensions",
            "tbl_sample_group_dimensions",
        }
        assert all(
            row["unit_status"] == "source_native_linked" for row in dimension_relations
        )
        assert all(row["dimension_relation_ids"] for row in rows)

        output = tmp_path / "normalized"
        with (
            patch.object(evidence_module, "_MAX_GOVERNED_FILE_BYTES", 16384),
            patch.object(evidence_module, "_PART_TARGET_BYTES", 6144),
        ):
            first = write_sead_source_native_evidence_bundle(
                acquisition, output, expected_identity=expected
            )
            first_bytes = {
                path.relative_to(output): path.read_bytes() for path in first
            }
            second = write_sead_source_native_evidence_bundle(
                acquisition, output, expected_identity=expected
            )
            assert first_bytes == {
                path.relative_to(output): path.read_bytes() for path in second
            }
            manifest = validate_sead_source_native_evidence_materialization(output)
            assert manifest["multipart_documents"]
            assert max(len(content) for content in first_bytes.values()) <= 16384
            observation_path = output / "source_native_observations.json"
            observation_document = json.loads(
                observation_path.read_text(encoding="utf-8")
            )
            observation_document["source_table_counts"]["tbl_abundances"] = 999
            observation_path.write_text(
                json.dumps(observation_document, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            manifest["source_table_count"] = 999
            manifest_records = manifest["files"]
            assert isinstance(manifest_records, list)
            for record in manifest_records:
                assert isinstance(record, dict)
                path = output / record["path"]
                content = path.read_bytes()
                record["byte_count"] = len(content)
                record["sha256"] = hashlib.sha256(content).hexdigest()
            manifest["file_set_sha256"] = evidence_module._stable_id(
                "sead-evidence-files",
                *(
                    f"{record['path']}:{record['sha256']}:{record['byte_count']}"
                    for record in sorted(
                        manifest_records, key=lambda item: item["path"]
                    )
                ),
            ).removeprefix("sead-evidence-files:")
            (output / "evidence_materialization_manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            with pytest.raises(ValueError, match="source table count"):
                validate_sead_source_native_evidence_materialization(output)
            for relative_path, content in first_bytes.items():
                (output / relative_path).write_bytes(content)
            multipart_path = next(path for path in first if path.parent != output)
            multipart_bytes = multipart_path.read_bytes()
            multipart_path.write_bytes(multipart_bytes + b" ")
            with pytest.raises(ValueError, match="byte count changed"):
                validate_sead_source_native_evidence_materialization(output)

        abundance_payload = acquisition / "payloads" / "tbl_abundances.json"
        abundance_payload.write_bytes(abundance_payload.read_bytes() + b" ")
        with pytest.raises(ValueError, match="byte_count"):
            build_sead_source_native_evidence_bundle(
                acquisition, expected_identity=expected
            )


@pytest.mark.parametrize(
    ("field", "forged_value"),
    (
        ("acquisition_bundle_sha256", "FORGED-NOT-A-DIGEST"),
        ("parent_admission_sha256", "8" * 64),
    ),
)
def test_source_native_evidence_recomputes_admission_identity_graph(
    tmp_path: Path, field: str, forged_value: str
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    with (
        patch.object(
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=(tmp_path / "admitted").resolve(),
            expected_identity=expected,
        )
        admission_path = admitted.output_root / "admission.json"
        document = json.loads(admission_path.read_text(encoding="utf-8"))
        document[field] = forged_value
        admission_path.write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="independently recomputed"):
            build_sead_source_native_evidence_bundle(
                admitted.output_root, expected_identity=expected
            )


def test_source_native_evidence_requires_bound_parent_admission(tmp_path: Path) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    with (
        patch.object(
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=(tmp_path / "admitted").resolve(),
            expected_identity=expected,
        )
        (admitted.output_root / "parent-admission.json").unlink()
        with pytest.raises(ValueError, match="missing or unmanifested files"):
            build_sead_source_native_evidence_bundle(
                admitted.output_root, expected_identity=expected
            )


def test_source_native_evidence_rejects_symlink_acquisition_root(
    tmp_path: Path,
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)
    with (
        patch.object(
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
            "_validate_country_accounting",
            return_value={"reconciles": True},
        ),
    ):
        admitted = materialize_sead_full_evidence_admission(
            snapshot,
            country_decisions_path=decisions,
            parent_admission_path=parent,
            output_root=(tmp_path / "admitted").resolve(),
            expected_identity=expected,
        )
        linked = tmp_path / "linked-acquisition"
        linked.symlink_to(admitted.output_root, target_is_directory=True)
        with pytest.raises(ValueError, match="symlink"):
            build_sead_source_native_evidence_bundle(
                linked.absolute(), expected_identity=expected
            )


def test_full_evidence_admission_validates_exact_profile_and_parent(
    tmp_path: Path,
) -> None:
    result = _acquire(tmp_path / "capture", _FullEvidencePostgrestFixture())
    snapshot = result.manifest_path.parent.resolve()
    decisions, parent, expected = _full_admission_inputs(snapshot, tmp_path)

    with (
        patch.object(
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
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
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
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
            admission_module,
            "_load_validated_boundary_authority",
            return_value=object(),
        ),
        patch.object(
            admission_module,
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
