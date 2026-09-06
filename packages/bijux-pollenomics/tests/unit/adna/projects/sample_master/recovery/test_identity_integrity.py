"""Tests for recovered sample identities, receipts, and normalized records."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.adna.projects.registry.archive_samples import (
    read_archive_project_samples,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.identity import _cell_value
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

from .support import SampleMasterRecoveryTestCase, expected_taxon_alignment

pytestmark = pytest.mark.generated_artifacts


class IdentityIntegrityTests(SampleMasterRecoveryTestCase):
    def test_materialized_lineage_components_are_unique(self) -> None:
        projects_root = self.data_root / "adna/governance/source_library/projects"
        duplicates = []
        for path in sorted(projects_root.glob("*/sample_master.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rows"]:
                for field in (
                    "sample_lineage_path",
                    "sample_lineage_locator",
                    "sample_lineage_excerpt",
                ):
                    components = [
                        component.strip()
                        for component in row[field].split(" || ")
                        if component.strip()
                    ]
                    if len(components) != len(set(components)):
                        duplicates.append(
                            (path.parent.name, row["repo_stable_sample_id"], field)
                        )

        self.assertFalse(duplicates)

    def test_recovery_target_raw_identity_taxonomy_and_receipts_close_exactly(
        self,
    ) -> None:
        archive_projects = (
            "PRJEB30282",
            "PRJEB31621",
            "PRJEB41594",
            "PRJEB59481",
            "PRJEB60484",
            "PRJEB75467",
            "PRJEB81815",
            "PRJNA705960",
            "SRP073444",
        )
        catalog = build_archive_project_catalog()
        catalog_species = {
            row.project_accession: row.species_latin_name for row in catalog
        }
        raw_expected: dict[tuple[str, str], tuple[str, str, str, str, str, str]] = {}
        for project_accession in archive_projects:
            logical_path = (
                self.data_root
                / "adna/governance/source_library/projects"
                / project_accession
                / "archive_metadata.html"
            )
            self.assert_source_receipt_closes(logical_path, project_accession)
            configured_species = catalog_species[project_accession]
            for raw_row in read_archive_project_samples(logical_path):
                names = " | ".join(raw_row.source_native_scientific_names)
                archive_source_identity = (
                    raw_row.archive_native_sample_id
                    or raw_row.archive_native_experiment_id
                )
                raw_expected[(project_accession, archive_source_identity)] = (
                    raw_row.archive_native_sample_id,
                    raw_row.archive_native_experiment_id,
                    raw_row.source_native_identity_kind,
                    " | ".join(raw_row.source_native_tax_ids),
                    names,
                    expected_taxon_alignment(configured_species, names),
                )

        cat_workbook = (
            self.data_root
            / "adna/governance/source_library/papers/10.1016-j.xgen.2025.101099/"
            "supplementary/1-s2.0-S2666979X25003556-mmc3.xlsx"
        )
        self.assert_source_receipt_closes(cat_workbook, "PRJNA1178732")
        cat_rows = _read_xlsx_rows(cat_workbook, sheet_name="A")
        cat_headers = {value.strip(): index for index, value in enumerate(cat_rows[2])}
        for worksheet_row in cat_rows[3:]:
            label = _cell_value(worksheet_row, cat_headers["Sample ID"])
            name = _cell_value(worksheet_row, cat_headers["Species"])
            if label and name:
                raw_expected[("PRJNA1178732", label)] = (
                    "",
                    "",
                    "biological_sample",
                    "",
                    name,
                    expected_taxon_alignment("Felis catus", name),
                )

        target_projects = (*archive_projects, "PRJNA1178732")
        master_rows = [
            row
            for project_accession in target_projects
            for row in build_project_sample_master_rows(
                self.data_root, project_accession
            )
        ]
        master_by_source_identity = {
            (
                row.project_accession,
                row.archive_native_sample_id
                or row.archive_native_experiment_id
                or row.supplementary_table_sample_label,
            ): row
            for row in master_rows
            if row.archive_native_sample_id
            or row.archive_native_experiment_id
            or row.sample_identity_resolution == "final"
        }
        self.assertEqual(len(raw_expected), 634)
        self.assertEqual(set(master_by_source_identity), set(raw_expected))
        for source_identity, expected_taxonomy in raw_expected.items():
            recovered_row = master_by_source_identity[source_identity]
            self.assertEqual(
                (
                    recovered_row.archive_native_sample_id,
                    recovered_row.archive_native_experiment_id,
                    recovered_row.source_native_identity_kind,
                    recovered_row.source_native_tax_id,
                    recovered_row.source_native_scientific_name,
                    recovered_row.taxon_alignment_status,
                ),
                expected_taxonomy,
                source_identity,
            )

        bundles = tuple(
            build_species_normalization_bundle(species)
            for species in (
                "horse",
                "pig",
                "sheep",
                "cattle",
                "goat",
                "dog",
                "cat",
                "camel",
                "reindeer",
                "donkey",
            )
        )
        normalized_rows = [row for bundle in bundles for row in bundle.sample_records]
        stable_tokens = [row.identity.stable_token for row in normalized_rows]
        normalized_by_master = {
            (row.project_accession, row.master_id): row for row in normalized_rows
        }
        self.assertEqual(len(stable_tokens), 1450)
        self.assertEqual(len(set(stable_tokens)), 1450)
        self.assertEqual(len(normalized_by_master), 1450)
        all_master_rows = [
            row
            for project in catalog
            for row in build_project_sample_master_rows(
                self.data_root, project.project_accession
            )
        ]
        admitted_master_by_identity = {
            (row.project_accession, row.repo_stable_sample_id): row
            for row in all_master_rows
            if row.sample_identity_resolution == "final"
            and row.sample_evidence_status != "experiment_level_only"
        }
        self.assertEqual(len(all_master_rows), 1475)
        self.assertEqual(len(admitted_master_by_identity), 1450)
        self.assertEqual(set(normalized_by_master), set(admitted_master_by_identity))
        for key, normalized in normalized_by_master.items():
            master_row = admitted_master_by_identity[key]
            self.assertEqual(
                (
                    normalized.source_native_tax_id,
                    normalized.source_native_scientific_name,
                    normalized.taxon_alignment_status,
                ),
                (
                    master_row.source_native_tax_id,
                    master_row.source_native_scientific_name,
                    master_row.taxon_alignment_status,
                ),
                key,
            )
