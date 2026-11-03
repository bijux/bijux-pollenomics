from __future__ import annotations

from collections import Counter
import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.workflow.normalization import (
    RECOVERED_SAMPLE_EVIDENCE_STATUSES,
)
from tests.support.repository import REPOSITORY_ROOT

from .marks import GENERATED_ARTIFACTS
from .support import build_tracked_animal_normalization_bundles

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_normalized_animal_samples_are_final_non_pollen_evidence(self) -> None:
        self.assertEqual(
            RECOVERED_SAMPLE_EVIDENCE_STATUSES,
            {"archive_native", "article_text_extracted", "direct_table_extracted"},
        )
        bundles = build_tracked_animal_normalization_bundles()
        samples = [sample for bundle in bundles for sample in bundle.sample_records]

        self.assertEqual(len(samples), 1468)
        self.assertEqual(
            sum(
                1
                for bundle in bundles
                for refusal in bundle.refusals
                if refusal.record_kind == "sample_record"
            ),
            25,
        )
        camel = next(
            bundle
            for bundle in bundles
            if bundle.species.latin_name == "Camelus dromedarius"
        )
        camel_sra_samples = [
            sample
            for sample in camel.sample_records
            if sample.project_accession == "SRP073444"
        ]
        self.assertEqual(len(camel_sra_samples), 18)
        self.assertTrue(
            all(
                sample.taxon_alignment_status == "project_species_match"
                for sample in camel_sra_samples
            )
        )
        self.assertTrue(
            all(sample.sample_identity_resolution == "final" for sample in samples)
        )
        self.assertTrue(
            all(
                sample.sample_evidence_status != "not_yet_recoverable"
                for sample in samples
            )
        )
        blocked_context = [
            sample
            for sample in samples
            if sample.inclusion_status == "sample_context_blocked"
        ]
        self.assertEqual(
            Counter(sample.inclusion_status for sample in samples),
            {
                "site_curated": 1065,
                "sample_context_blocked": 378,
                "comparator_site_curated": 20,
                "nordic_lead_site_curated": 5,
            },
        )
        self.assertTrue(
            all(sample.inclusion_note.strip() for sample in blocked_context)
        )
        self.assertEqual(
            sum(sample.locality is not None for sample in blocked_context),
            319,
        )
        for bundle in bundles:
            payload = bundle.as_dict()
            self.assertEqual(payload["evidence_domain"], "animal_ancient_dna")
            self.assertFalse(payload["pollen_eligible"])
            self.assertFalse(payload["pollen_propagation_eligible"])

    def test_locality_summaries_require_identity_and_unique_sample_membership(
        self,
    ) -> None:
        bundles = build_tracked_animal_normalization_bundles()

        self.assertTrue(
            all(
                locality.locality is not None and locality.locality.strip()
                for bundle in bundles
                for locality in bundle.locality_records
            )
        )
        memberships = Counter(
            (locality.project_accessions, sample_id)
            for bundle in bundles
            for locality in bundle.locality_records
            for sample_id in locality.sample_ids
        )
        self.assertFalse(
            {
                membership: count
                for membership, count in memberships.items()
                if count > 1
            }
        )
        invalid_memberships = []
        for bundle in bundles:
            sample_projects = {
                sample.master_id: sample.project_accession
                for sample in bundle.sample_records
            }
            for locality in bundle.locality_records:
                for sample_id in locality.sample_ids:
                    if (
                        sample_projects.get(sample_id)
                        not in locality.project_accessions
                    ):
                        invalid_memberships.append(
                            (bundle.species.latin_name, locality.locality, sample_id)
                        )
        self.assertFalse(invalid_memberships)
        camel = next(
            bundle
            for bundle in bundles
            if bundle.species.latin_name == "Camelus dromedarius"
        )
        camel_localities = [
            locality
            for locality in camel.locality_records
            if "SRP073444" in locality.project_accessions
        ]
        self.assertEqual(len(camel_localities), 7)
        self.assertEqual(sum(len(row.sample_ids) for row in camel_localities), 18)
        self.assertTrue(
            all(
                row.locality is not None and "Wadi" not in row.locality
                for row in camel_localities
            )
        )

    def test_pig_site_localities_preserve_admitted_archaeological_basis(self) -> None:
        bundle = build_species_normalization_bundle("pig")
        source_sites = {
            locality.locality: locality
            for locality in bundle.locality_records
            if locality.project_accessions == ("PRJEB30282",)
        }
        samples = {sample.master_id: sample for sample in bundle.sample_records}
        admitted_statuses = {
            "comparator_site_curated",
            "nordic_lead_site_curated",
            "site_curated",
        }
        pig_sites = {
            name: locality
            for name, locality in source_sites.items()
            if any(
                samples[sample_id].inclusion_status in admitted_statuses
                for sample_id in locality.sample_ids
            )
        }

        self.assertEqual(len(source_sites), 105)
        self.assertEqual(
            sum(
                all(
                    samples[sample_id].inclusion_status == "sample_context_blocked"
                    for sample_id in locality.sample_ids
                )
                for locality in source_sites.values()
            ),
            103,
        )
        self.assertEqual(set(pig_sites), {"Bundsø", "Trelleborg"})
        self.assertEqual(
            {
                name: (
                    locality.time_start_bp,
                    locality.time_end_bp,
                    locality.dating_basis,
                    locality.chronology.evidence_class,
                    locality.chronology.precision_posture,
                )
                for name, locality in pig_sites.items()
            },
            {
                "Bundsø": (
                    4700,
                    4700,
                    "locality_sample_coverage",
                    "locality_sample_coverage_hull",
                    "display_coverage_only",
                ),
                "Trelleborg": (
                    1000,
                    1000,
                    "locality_sample_coverage",
                    "locality_sample_coverage_hull",
                    "display_coverage_only",
                ),
            },
        )
        for locality in pig_sites.values():
            self.assertTrue(locality.sample_chronologies)
            for support in locality.sample_chronologies:
                sample = samples[support.sample_id]
                self.assertEqual(support.chronology, sample.chronology)
                self.assertEqual(
                    support.chronology.dating_basis, "archaeological_context"
                )
                self.assertEqual(
                    support.chronology.evidence_class, "archaeological_context_date"
                )
                self.assertEqual(
                    support.chronology.precision_posture,
                    "sample_approximate_or_modeled",
                )

    def test_aurochs_samples_preserve_source_means_and_locality_dating_basis(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("cattle")
        samples = {
            sample.archive_native_sample_id: sample
            for sample in bundle.sample_records
            if sample.project_accession == "PRJEB75467"
            and sample.archive_native_sample_id
        }

        normalized_means = {
            accession: sample.time_mean_bp
            for accession, sample in samples.items()
            if sample.time_mean_bp is not None
        }
        source_means = {
            row.repo_stable_sample_id.rsplit(":", 1)[-1].upper(): row.time_mean_bp
            for row in build_project_sample_chronology_rows(
                REPOSITORY_ROOT / "data", "PRJEB75467"
            )
            if row.time_mean_bp is not None
            and row.sample_identity_resolution == "final"
        }

        self.assertEqual(len(source_means), 33)
        self.assertEqual(normalized_means, source_means)
        self.assertEqual(
            {
                accession: normalized_means[accession]
                for accession in (
                    "SAMEA115574419",
                    "SAMEA115574441",
                    "SAMEA115574442",
                    "SAMEA115574456",
                    "SAMEA115574457",
                )
            },
            {
                "SAMEA115574419": 8074,
                "SAMEA115574441": 9334,
                "SAMEA115574442": 9546,
                "SAMEA115574456": 7302,
                "SAMEA115574457": 7296,
            },
        )
        self.assertNotIn("SAMEA115574447", normalized_means)
        self.assertTrue(
            all(
                sample.time_start_bp <= sample.time_mean_bp <= sample.time_end_bp
                for sample in samples.values()
                if sample.time_start_bp is not None
                and sample.time_mean_bp is not None
                and sample.time_end_bp is not None
            )
        )
        self.assertEqual(
            samples["SAMEA115574456"].dating_basis,
            "mitochondrial_phylogenetic_model",
        )
        self.assertEqual(
            {
                sample.coordinate_confidence
                for sample in samples.values()
                if sample.latitude is not None
            },
            {"approximate"},
        )
        all_localities = {
            locality.locality: locality
            for locality in bundle.locality_records
            if locality.project_accessions == ("PRJEB75467",)
        }
        admitted_locality_names = {
            "Hjørring, Tofte Bæk",
            "Lundby I",
            "Nevishög",
            "Skåne",
        }
        localities = {
            name: locality
            for name, locality in all_localities.items()
            if name in admitted_locality_names
        }
        self.assertEqual(
            {
                name: {
                    support.chronology.dating_basis
                    for support in locality.sample_chronologies
                }
                for name, locality in localities.items()
            },
            {
                "Hjørring, Tofte Bæk": {"radiocarbon"},
                "Lundby I": {"mitochondrial_phylogenetic_model"},
                "Nevishög": {"radiocarbon"},
                "Skåne": {"radiocarbon"},
            },
        )
        for locality in localities.values():
            self.assertEqual(locality.dating_basis, "locality_sample_coverage")
            self.assertEqual(
                locality.chronology.evidence_class, "locality_sample_coverage_hull"
            )
            self.assertEqual(
                locality.chronology.precision_posture, "display_coverage_only"
            )
            for support in locality.sample_chronologies:
                sample = next(
                    sample
                    for sample in samples.values()
                    if sample.master_id == support.sample_id
                )
                self.assertEqual(support.chronology, sample.chronology)
        self.assertEqual(
            {locality.coordinate_confidence for locality in localities.values()},
            {"approximate"},
        )
        self.assertNotIn(
            "Frederiksborg, Alsønderup",
            all_localities,
        )
        self.assertTrue(
            any(
                refusal.reason == "locality_depends_on_nonfinal_sample_identity"
                and "Frederiksborg, Alsønderup" in refusal.source_token
                for refusal in bundle.refusals
            )
        )
        self.assertNotIn("", all_localities)
        self.assertTrue(
            any(
                refusal.reason == "locality_text_not_evidenced"
                and refusal.source_token == "PRJEB75467:unresolved"
                for refusal in bundle.refusals
            )
        )
