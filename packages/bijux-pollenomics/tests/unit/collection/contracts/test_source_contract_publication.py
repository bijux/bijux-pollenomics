from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.governance.contracts import (
    build_adna_governance_role_registry,
    build_source_library_project_surface_contract,
    materialize_adna_governance_contracts,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.contracts.capabilities import (
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
    SEAD_NORMALIZED_EVIDENCE_EVENTS,
    SEAD_NORMALIZED_EVIDENCE_MANIFEST,
    SEAD_NORMALIZED_OBSERVATIONS,
    SEAD_NORMALIZED_RELATIONS,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contracts,
    build_source_family_state_matrix_payload,
)
from bijux_pollenomics.collection.contracts.repository import (
    build_evidence_artifact_contract_payload,
    build_source_fact_ownership_payload,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    AadrReleaseManifestIdentity,
    build_aadr_source_accountability_receipt,
    canonical_aadr_source_accountability_bytes,
)
from bijux_pollenomics.collection.sources.aadr.materialization.source_rows import (
    load_aadr_source_table,
)

_AADR_TEST_HEADER = "\t".join(
    (
        "Genetic ID",
        "Political Entity",
        "Method for Determining Date",
        "Date mean in BP",
        "Date standard deviation in BP",
        "Full Date",
        "Latitude",
        "Longitude",
    )
)


def _write_aadr_accountability_fixture(
    output_root: Path,
    *,
    source_release: str,
    receipt_version: str | None = None,
) -> tuple[Path, Path]:
    release_root = output_root / "aadr" / source_release
    manifest_path = release_root / "release_manifest.json"
    panel_path = release_root / "ho" / "ho.anno"
    panel_path.parent.mkdir(parents=True)
    manifest_bytes = (
        json.dumps({"source": "AADR", "requested_version": source_release}) + "\n"
    ).encode()
    panel_bytes = (_AADR_TEST_HEADER + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)
    panel_path.write_bytes(panel_bytes)
    panel = load_aadr_source_table(
        panel_path,
        source_release=source_release,
        dataset_name="ho",
        logical_source_path=f"data/aadr/{source_release}/ho/ho.anno",
    )
    receipt = build_aadr_source_accountability_receipt(
        reconcile_aadr_panels((panel,)),
        release_manifest=AadrReleaseManifestIdentity(
            logical_path=f"data/aadr/{source_release}/release_manifest.json",
            source_release=source_release,
            sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            byte_count=len(manifest_bytes),
        ),
    )
    receipt_path = (
        output_root
        / "adna/species/homo_sapiens/review"
        / f"aadr_{receipt_version or source_release}_source_accountability.json"
    )
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_bytes(canonical_aadr_source_accountability_bytes(receipt))
    return receipt_path, panel_path


class SourceContractPublicationTests(unittest.TestCase):
    def test_sead_publication_requires_only_the_invariant_site_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            output_root = workspace / "data"
            contract = next(
                contract
                for contract in build_source_family_contracts()
                if contract.source_key == "sead"
            )
            for layer in (
                contract.raw_layer,
                contract.normalized_layer,
                contract.reviewed_layer,
                contract.published_layer,
            ):
                for relative_path in layer.example_artifacts:
                    path = workspace / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}", encoding="utf-8")

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"sead_point_count": 4},
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "sead")
        self.assertEqual(row["published_status"], "present")
        self.assertEqual(row["publication_posture"], "published_with_review_support")
        self.assertNotIn("missing_published_surface", row["blocking_reasons"])

    def test_stale_raa_and_boundary_files_do_not_admit_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            output_root = workspace / "data"
            artifact_paths = (
                output_root / "raa/raw/fornsok_domains.json",
                output_root / "raa/normalized/sweden_archaeology_layer.json",
                output_root / "raa/review/spatiotemporal_review.json",
                workspace
                / "docs/report/regions/nordic/sweden_archaeology_density.geojson",
                output_root / "boundaries/raw/sweden.geojson",
                output_root / "boundaries/normalized/nordic_country_boundaries.geojson",
                output_root / "boundaries/review/framing_review.json",
                workspace
                / "docs/report/regions/nordic/nordic_country_boundaries.geojson",
            )
            for path in artifact_paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={
                    "raa_total_site_count": 761_917,
                    "raa_heritage_site_count": 318_265,
                },
            )

        rows = {row["source_key"]: row for row in payload["rows"]}
        for source_key in ("raa", "boundaries"):
            row = rows[source_key]
            self.assertEqual(row["authority_status"], "refused")
            self.assertEqual(
                row["publication_posture"], "refused_not_publication_ready"
            )
            self.assertIn("source_authority_refused", row["blocking_reasons"])
        self.assertEqual(rows["raa"]["published_status"], "refused")
        self.assertEqual(rows["boundaries"]["published_status"], "present")
        self.assertEqual(
            rows["raa"]["coverage_metrics"],
            {"raa_total_site_count": None, "raa_heritage_site_count": None},
        )
        self.assertEqual(
            rows["boundaries"]["coverage_metrics"]["boundary_country_count"],
            None,
        )

    def test_svar_requires_reconciled_counts_and_digest_bound_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            output_root = workspace / "data"
            registry_path = output_root / "svar/normalized/sweden_lake_registry.geojson"
            registry_path.parent.mkdir(parents=True)
            registry_payload = {
                "type": "FeatureCollection",
                "features": [{"id": "lake-1"}, {"id": "lake-2"}],
            }
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")
            manifest_path = output_root / "svar/raw/svar_lake_registry_manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "source": "SMHI SVAR",
                        "matched_lake_count": 2,
                        "normalized_lake_count": 2,
                    }
                ),
                encoding="utf-8",
            )
            (registry_path.parent / "svar_summary.json").write_text(
                json.dumps({"source": "SMHI SVAR", "lake_count": 2}),
                encoding="utf-8",
            )
            review_root = output_root / "svar/review"
            review_root.mkdir(parents=True)
            (review_root / "sweden_lake_candidate_registry.geojson").write_text(
                json.dumps({"type": "FeatureCollection", "features": [{"id": 1}]}),
                encoding="utf-8",
            )
            review_path = review_root / "lake_candidate_registry_review.json"
            review_path.write_text(
                json.dumps({"source": "SMHI SVAR", "source_lake_count": 2}),
                encoding="utf-8",
            )
            published_path = (
                workspace
                / "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.geojson"
            )
            published_path.parent.mkdir(parents=True)
            published_path.write_text("{}", encoding="utf-8")

            pending_payload = build_source_family_state_matrix_payload(
                output_root, counts={"svar_lake_count": 99_999}
            )
            review_path.write_text(
                json.dumps(
                    {
                        "source": "SMHI SVAR",
                        "source_lake_count": 2,
                        "registry_sha256": hashlib.sha256(
                            registry_path.read_bytes()
                        ).hexdigest(),
                        "release_status": "accepted",
                        "reviewer_id": "qualified-reviewer",
                    }
                ),
                encoding="utf-8",
            )
            admitted_payload = build_source_family_state_matrix_payload(
                output_root, counts={"svar_lake_count": 99_999}
            )

        pending = next(
            row for row in pending_payload["rows"] if row["source_key"] == "svar"
        )
        admitted = next(
            row for row in admitted_payload["rows"] if row["source_key"] == "svar"
        )
        self.assertEqual(pending["authority_status"], "review_required")
        self.assertEqual(
            pending["publication_posture"], "review_required_not_publication_ready"
        )
        self.assertEqual(pending["coverage_metrics"]["svar_lake_count"], 2)
        self.assertEqual(admitted["authority_status"], "admitted")
        self.assertEqual(
            admitted["publication_posture"], "published_with_review_support"
        )

    def test_state_matrix_does_not_use_its_own_output_as_review_evidence(self) -> None:
        contracts = {
            contract.source_key: contract
            for contract in build_source_family_contracts()
        }

        for source_key in ("boundaries", "landclim", "raa", "svar"):
            reviewed = contracts[source_key].reviewed_layer
            self.assertNotIn(
                "source_family_evidence_stage_matrix.json",
                reviewed.example_artifacts,
            )

    def test_state_matrix_reports_animal_sample_foundation_rows(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            output_root = Path(workspace_dir) / "data"
            truth_path = (
                output_root
                / "adna"
                / "governance"
                / "animal_sample_foundation_truth.json"
            )
            truth_path.parent.mkdir(parents=True)
            truth_path.write_text(
                '{"summary": {"sample_row_count": 37}}',
                encoding="utf-8",
            )

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={},
            )

        animal_row = next(
            row for row in payload["rows"] if row["source_key"] == "animal_adna"
        )
        self.assertEqual(animal_row["coverage_metrics"]["animal_sample_count"], 37)

    def test_fact_and_artifact_contract_payloads_choose_governing_surfaces(
        self,
    ) -> None:
        fact_payload = build_source_fact_ownership_payload()
        artifact_payload = build_evidence_artifact_contract_payload()

        self.assertEqual(
            fact_payload["schema_version"], "source-fact-ownership-registry.v1"
        )
        self.assertEqual(
            artifact_payload["schema_version"], "evidence-artifact-contracts.v1"
        )
        fact_keys = {row["fact_key"] for row in fact_payload["rows"]}
        artifact_keys = {row["artifact_key"] for row in artifact_payload["rows"]}
        self.assertIn("animal_sample_identity", fact_keys)
        self.assertIn("country_publication_bundle", artifact_keys)

        facts = {row["fact_key"]: row for row in fact_payload["rows"]}
        self.assertEqual(
            facts["sead_archaeology_context"]["governing_surface_path"],
            SEAD_NORMALIZED_EVIDENCE_MANIFEST,
        )
        self.assertEqual(
            facts["sead_source_native_observations"]["governing_surface_path"],
            SEAD_NORMALIZED_OBSERVATIONS,
        )
        self.assertEqual(
            facts["sead_observation_relations"]["governing_surface_path"],
            SEAD_NORMALIZED_RELATIONS,
        )
        self.assertEqual(
            facts["sead_evidence_event_disposition"]["governing_surface_path"],
            SEAD_NORMALIZED_EVIDENCE_EVENTS,
        )
        self.assertIn(
            SEAD_ADMITTED_ACQUISITION_ADMISSION,
            facts["sead_archaeology_context"]["supporting_surface_paths"],
        )

    def test_materialize_adna_governance_contracts_writes_role_and_project_contracts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            project_root = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            project_root.mkdir(parents=True, exist_ok=True)
            for filename in (
                "bundle_manifest.json",
                "intake_dossier.json",
                "curation_note.md",
                "sample_master.json",
                "sample_master.csv",
                "sample_sites.json",
                "sample_sites.csv",
                "locality_worksheet.json",
                "locality_worksheet.csv",
                "sample_locality_evidence.json",
                "sample_locality_evidence.csv",
                "sample_chronology.json",
                "sample_chronology.csv",
                "sample_chronology_evidence.json",
                "sample_chronology_evidence.csv",
                "sample_chronology_provenance.json",
                "sample_chronology_provenance.csv",
            ):
                (project_root / filename).write_text("{}", encoding="utf-8")

            materialize_adna_governance_contracts(output_root)

            self.assertTrue(
                (
                    output_root / "adna" / "governance" / "surface_role_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_surface_contract.json"
                ).is_file()
            )
            role_payload = build_adna_governance_role_registry()
            project_contract = build_source_library_project_surface_contract()

        self.assertEqual(
            role_payload["schema_version"], "adna-governance-role-registry.v1"
        )
        self.assertEqual(
            project_contract["schema_version"],
            "source-library-project-surface-contract.v1",
        )
