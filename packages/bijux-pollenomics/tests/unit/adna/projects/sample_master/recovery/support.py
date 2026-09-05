"""Shared assertions for sample-master recovery tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tests.support.repository import REPOSITORY_ROOT

from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    resolve_source_artifact_path,
)


class SampleMasterRecoveryTestCase(unittest.TestCase):
    """Base test case exposing governed data and receipt assertions."""

    data_root = REPOSITORY_ROOT / "data"

    def assert_source_receipt_closes(
        self,
        logical_path: Path,
        project_accession: str,
    ) -> None:
        receipt_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        logical_payload = read_source_artifact_bytes(logical_path)
        stored_path = resolve_source_artifact_path(logical_path)
        stored_payload = stored_path.read_bytes()
        receipt_projects = (
            receipt["project_accession"]
            if "project_accession" in receipt
            else receipt["project_accessions"]
        )
        expected_projects: str | list[str] = (
            project_accession if "project_accession" in receipt else [project_accession]
        )
        self.assertEqual(receipt_projects, expected_projects)
        self.assertEqual(receipt["byte_size"], len(logical_payload))
        self.assertEqual(
            receipt["content_sha256"], hashlib.sha256(logical_payload).hexdigest()
        )
        self.assertEqual(receipt["storage_byte_size"], len(stored_payload))
        self.assertEqual(
            receipt["storage_sha256"], hashlib.sha256(stored_payload).hexdigest()
        )
        bundle_path = (
            self.data_root
            / "adna/governance/source_library/projects"
            / project_accession
            / "bundle_manifest.json"
        )
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        self.assertIn(
            str(logical_path.relative_to(self.data_root)),
            bundle["local_artifact_paths"],
        )


def expected_taxon_alignment(configured_species: str, source_names: str) -> str:
    """Return the expected source-to-project taxonomy alignment status."""
    names = tuple(name.strip() for name in source_names.split(" | ") if name.strip())
    if not names:
        return "not_reported"
    if len(names) > 1:
        return "archive_taxon_conflict"
    if names[0].casefold() == configured_species.casefold():
        return "project_species_match"
    return "project_species_mismatch"
