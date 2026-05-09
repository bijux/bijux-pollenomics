from __future__ import annotations

from pathlib import Path
import unittest

import pytest

from bijux_pollenomics.foundation import (
    DISALLOWED_PUBLIC_ARTIFACT_TOKENS,
    PUBLIC_INFORMATION_ROLE_MEANINGS,
    audit_public_artifact_inventory,
    infer_public_information_role,
    validate_public_artifact_stem,
)

pytestmark = pytest.mark.generated_artifacts


class PublicArtifactLanguageUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[4]

    def test_role_taxonomy_and_disallowed_tokens_stay_explicit(self) -> None:
        self.assertIn("review", PUBLIC_INFORMATION_ROLE_MEANINGS)
        self.assertIn("validation", PUBLIC_INFORMATION_ROLE_MEANINGS)
        self.assertIn("truth", PUBLIC_INFORMATION_ROLE_MEANINGS)
        self.assertIn("packets", DISALLOWED_PUBLIC_ARTIFACT_TOKENS)
        self.assertIn("viewer", DISALLOWED_PUBLIC_ARTIFACT_TOKENS)
        self.assertEqual(
            infer_public_information_role("animal_point_evidence_review"),
            "review",
        )
        self.assertEqual(
            infer_public_information_role("repository_docs_scope_validation"),
            "validation",
        )
        self.assertEqual(
            validate_public_artifact_stem("animal_point_evidence_review"),
            (),
        )
        self.assertIn(
            "disallowed_tokens:viewer",
            validate_public_artifact_stem("animal_sample_chronology_viewer"),
        )

    def test_public_artifact_inventory_stays_free_of_old_delivery_terms(self) -> None:
        findings = audit_public_artifact_inventory(self.repo_root)
        self.assertGreaterEqual(len(findings), 40)
        invalid = [finding for finding in findings if finding.issues]
        self.assertEqual(
            invalid,
            [],
            "\n".join(
                f"{finding.artifact_path}: {', '.join(finding.issues)}"
                for finding in invalid
            ),
        )
