from __future__ import annotations

from collections import Counter
import json
import re
import unittest

import pytest

from .repository_paths import REPO_ROOT


pytestmark = pytest.mark.generated_artifacts


def _load_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _normalized_markdown(relative_path: str) -> str:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    return " ".join(text.split())


def _claim_blocks(text: str) -> tuple[str, ...]:
    blocks: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        lines = tuple(line.strip() for line in paragraph.splitlines() if line.strip())
        if lines and all(line.startswith("|") for line in lines):
            blocks.extend(lines)
        elif lines:
            blocks.append(" ".join(lines))
    return tuple(blocks)


class PublicAnimalClaimParityTests(unittest.TestCase):
    def test_public_summary_matches_governed_animal_populations(self) -> None:
        candidates = _load_json(
            "data/adna/final/atlas/animal_atlas_point_candidates.json"
        )
        accountability = _load_json(
            "data/adna/final/atlas/animal_atlas_candidate_accountability.json"
        )
        readiness = _load_json(
            "data/adna/governance/cross_species_map_readiness.json"
        )
        foundation = _load_json(
            "data/adna/governance/animal_sample_foundation_truth.json"
        )
        sample_master = _load_json(
            "data/adna/governance/source_library/"
            "project_sample_master_completeness.json"
        )

        candidate_rows = candidates["rows"]
        self.assertIsInstance(candidate_rows, list)
        sample_ids = {
            sample_id
            for row in candidate_rows
            for sample_id in row["sample_record_ids"]
        }
        scope_counts = Counter(row["animal_scope"] for row in candidate_rows)
        readiness_totals = readiness["totals"]
        foundation_summary = foundation["summary"]
        project_rows = sample_master["rows"]

        published_features = len(candidate_rows)
        mapped_samples = len(sample_ids)
        recovered_raw = sum(row["recovered_sample_count"] for row in project_rows)
        final_samples = sum(row["final_sample_count"] for row in project_rows)
        contributing_projects = sum(
            row["final_sample_count"] > 0 for row in project_rows
        )

        self.assertEqual(candidates["row_count"], published_features)
        self.assertEqual(accountability["candidate_row_count"], published_features)
        self.assertEqual(accountability["passed_row_count"], published_features)
        self.assertTrue(accountability["overall_ok"])
        self.assertEqual(
            readiness_totals["publication_candidate_count"], published_features
        )
        self.assertEqual(
            readiness_totals["coordinate_provenance_mappable_count"],
            published_features + readiness_totals["not_materialized_count"],
        )
        self.assertEqual(
            readiness_totals["coordinate_provenance_row_count"],
            readiness_totals["coordinate_provenance_mappable_count"]
            + readiness_totals["refused_coordinate_provenance_count"],
        )
        self.assertEqual(final_samples, foundation_summary["sample_row_count"])

        overview = _normalized_markdown(
            "docs/public/pollenomics-data/overview/animal-ancient-dna-evidence.md"
        )
        required_claims = (
            f"**{final_samples:,} final sample rows**",
            f"**{foundation_summary['tracked_species_count']:,} species and "
            f"{contributing_projects:,} contributing projects**",
            f"**{len(project_rows):,} tracked projects**",
            f"**{recovered_raw:,} recovered raw sample-master rows**",
            f"**{published_features:,} published locality features**",
            f"**{mapped_samples:,} distinct admitted samples**",
            f"{scope_counts['domesticated_core']:,} `domesticated_core` localities",
            f"{scope_counts['wild_or_progenitor_context']:,} "
            "`wild_or_progenitor_context` localities",
        )
        for claim in required_claims:
            with self.subTest(claim=claim):
                self.assertIn(claim, overview)

        coordinates = _normalized_markdown(
            "docs/public/pollenomics-data/evidence/coordinates.md"
        )
        self.assertIn(
            f"{readiness_totals['coordinate_provenance_row_count']:,} "
            "coordinate-provenance rows therefore reconcile to "
            f"{readiness_totals['coordinate_provenance_mappable_count']:,} "
            "mappable and "
            f"{readiness_totals['refused_coordinate_provenance_count']:,} refused",
            coordinates,
        )

    def test_public_docs_reject_superseded_animal_count_semantics(self) -> None:
        public_root = REPO_ROOT / "docs" / "public"
        stale_patterns = {
            "legacy point publication total": re.compile(
                r"(?:\b(?:233|234)\b.{0,120}\b(?:animal|point|publication|"
                r"candidate|sample-backed)\b|\b(?:animal|point|publication|"
                r"candidate|sample-backed)\b.{0,120}\b(?:233|234)\b)",
                re.IGNORECASE,
            ),
            "legacy foundation total": re.compile(
                r"(?:\b894\b.{0,100}\bfoundation\b|"
                r"\bfoundation\b.{0,100}\b894\b)",
                re.IGNORECASE,
            ),
            "legacy recovered-sample total": re.compile(
                r"(?:\b868\b.{0,100}\b(?:recovered|sample-master|sample rows)\b|"
                r"\b(?:recovered|sample-master|sample rows)\b.{0,100}\b868\b)",
                re.IGNORECASE,
            ),
        }

        for path in sorted(public_root.rglob("*.md")):
            text = " ".join(path.read_text(encoding="utf-8").split())
            for label, pattern in stale_patterns.items():
                with self.subTest(path=path.relative_to(REPO_ROOT), claim=label):
                    self.assertIsNone(pattern.search(text))

    def test_wadi_halfa_remains_an_accounted_non_member(self) -> None:
        candidates = _load_json(
            "data/adna/final/atlas/animal_atlas_point_candidates.json"
        )
        readiness = _load_json(
            "data/adna/governance/cross_species_map_readiness.json"
        )
        wadi_rows = [
            row
            for row in readiness["not_materialized_rows"]
            if row["project_accession"] == "SRP073444"
        ]
        self.assertEqual(len(wadi_rows), 1)
        reason_code = wadi_rows[0]["reason_code"]
        self.assertEqual(reason_code, "no_admitted_sample_backed_locality_candidate")
        self.assertFalse(
            any(
                "Wadi Halfa" in row["locality"]
                or row["primary_project_accession"] == "SRP073444"
                for row in candidates["rows"]
            )
        )

        public_root = REPO_ROOT / "docs" / "public"
        wadi_docs = []
        affirmative_publication = re.compile(
            r"(?:Wadi Halfa provisional feature|"
            r"Wadi Halfa[^.]{0,180}(?:published geometry|spatially admitted|"
            r"admitted (?:as|under)|qualified (?:project-)?context "
            r"(?:feature|point|member|spatial presence)|"
            r"qualified as project context)|"
            r"(?:single )?dromedary feature[^.]{0,100}Wadi Halfa[^.]{0,100}"
            r"(?:is )?admitted)",
            re.IGNORECASE,
        )
        for path in sorted(public_root.rglob("*.md")):
            source_text = path.read_text(encoding="utf-8")
            text = " ".join(source_text.split())
            if "Wadi Halfa" not in text:
                continue
            wadi_docs.append(path)
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertIn(reason_code, text)
                self.assertFalse(
                    any(
                        affirmative_publication.search(block)
                        for block in _claim_blocks(source_text)
                        if "Wadi Halfa" in block
                    )
                )

        self.assertTrue(wadi_docs)


if __name__ == "__main__":
    unittest.main()
