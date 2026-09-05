from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    materialize_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    service as admission_service,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    build_sead_source_native_evidence_bundle,
    validate_sead_source_native_evidence_materialization,
    write_sead_source_native_evidence_bundle,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    publication as evidence_publication,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    serialization as evidence_serialization,
)

from .support import _FullEvidencePostgrestFixture, _acquire, _full_admission_inputs


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
            patch.object(evidence_publication, "_MAX_GOVERNED_FILE_BYTES", 16384),
            patch.object(evidence_publication, "_PART_TARGET_BYTES", 6144),
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
            manifest["file_set_sha256"] = evidence_serialization._stable_id(
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
