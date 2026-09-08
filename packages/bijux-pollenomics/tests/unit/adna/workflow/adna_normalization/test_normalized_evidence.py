from __future__ import annotations

from collections import Counter
from types import SimpleNamespace
import unittest

from bijux_pollenomics.adna import AdnaChronology, build_species_normalization_bundle
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.workflow.normalization import (
    RECOVERED_SAMPLE_EVIDENCE_STATUSES,
)
from bijux_pollenomics.adna.workflow.normalization.samples import (
    _chronology_with_source_mean,
)
from tests.support.repository import REPOSITORY_ROOT

from .marks import GENERATED_ARTIFACTS
from .support import build_tracked_animal_normalization_bundles

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_mixed_radiocarbon_and_context_locality_uses_governed_basis(self) -> None:
        from bijux_pollenomics.adna.workflow.normalization.localities import (
            _locality_dating_basis,
        )

        rows = [
            SimpleNamespace(
                time_start_bp=6000,
                time_end_bp=6100,
                dating_basis="radiocarbon",
            ),
            SimpleNamespace(
                time_start_bp=5900,
                time_end_bp=6000,
                dating_basis="archaeological_context",
            ),
        ]

        self.assertEqual(
            _locality_dating_basis(
                rows,
                fallback="historical_and_archaeological_context",
            ),
            "mixed_radiocarbon_and_archaeological_context",
        )

    def test_locality_envelope_of_point_dates_is_not_a_precise_point(self) -> None:
        from bijux_pollenomics.adna.workflow.normalization.chronology import (
            _aggregate_locality_precision_posture,
        )

        chronology = AdnaChronology(
            original_text="100-200 BP",
            time_start_bp=100,
            time_end_bp=200,
            time_mean_bp=150,
            dating_basis="radiocarbon",
        )
        rows = [
            SimpleNamespace(chronology_precision_posture="sample_precise_point"),
            SimpleNamespace(chronology_precision_posture="sample_precise_point"),
        ]

        self.assertEqual(
            _aggregate_locality_precision_posture(rows, chronology),
            "sample_precise_interval",
        )

    def test_tilde_marked_chronology_remains_approximate(self) -> None:
        from bijux_pollenomics.adna.workflow.normalization.chronology import (
            _fallback_chronology_precision_posture,
        )

        chronology = AdnaChronology(
            original_text="~3500 - 1800 BCE",
            time_start_bp=3749,
            time_end_bp=5449,
            time_mean_bp=4599,
            dating_basis="archaeological_context",
        )

        self.assertEqual(
            _fallback_chronology_precision_posture(chronology),
            "sample_approximate_or_modeled",
        )

        from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
            _precision_posture_for,
        )

        self.assertEqual(
            _precision_posture_for(
                chronology_text=chronology.original_text,
                chronology=chronology,
                chronology_strength="sample_owned_interval",
                chronology_evidence_class="historical_or_recent_date",
                chronology_normalization_status="normalized_interval",
            ),
            "sample_approximate_or_modeled",
        )

    def test_locality_with_finite_and_censored_claims_fails_numeric_comparison(
        self,
    ) -> None:
        from bijux_pollenomics.adna.workflow.normalization.chronology import (
            _aggregate_locality_chronology,
        )

        sample_rows = (
            SimpleNamespace(stable_sample_id="finite"),
            SimpleNamespace(stable_sample_id="censored"),
        )
        chronology_lookup = {
            "finite": SimpleNamespace(
                chronology_text="30517 BP",
                time_start_bp=30517,
                time_end_bp=30517,
                chronology_evidence_class="direct_radiocarbon_date",
                chronology_precision_posture="sample_precise_point",
            ),
            "censored": SimpleNamespace(
                chronology_text=">51700 BP",
                time_start_bp=None,
                time_end_bp=None,
                chronology_evidence_class="unresolved",
                chronology_precision_posture="sample_approximate_or_modeled",
            ),
        }

        chronology = _aggregate_locality_chronology(
            sample_rows=sample_rows,
            chronology_lookup=chronology_lookup,
            fallback_text="",
            fallback_start_bp=None,
            fallback_end_bp=None,
            dating_basis="radiocarbon",
        )

        self.assertEqual(chronology.original_text, "30517 BP; >51700 BP")
        self.assertIsNone(chronology.time_start_bp)
        self.assertIsNone(chronology.time_end_bp)
        self.assertIsNone(chronology.time_mean_bp)
        self.assertEqual(chronology.evidence_class, "unresolved")
        self.assertEqual(
            chronology.precision_posture,
            "sample_approximate_or_modeled",
        )

    def test_normalized_animal_samples_are_final_non_pollen_evidence(self) -> None:
        self.assertEqual(
            RECOVERED_SAMPLE_EVIDENCE_STATUSES,
            {"archive_native", "article_text_extracted", "direct_table_extracted"},
        )
        bundles = build_tracked_animal_normalization_bundles()
        samples = [sample for bundle in bundles for sample in bundle.sample_records]

        self.assertEqual(len(samples), 1450)
        self.assertEqual(
            sum(
                1
                for bundle in bundles
                for refusal in bundle.refusals
                if refusal.record_kind == "sample_record"
            ),
            43,
        )
        camel = next(
            bundle
            for bundle in bundles
            if bundle.species.latin_name == "Camelus dromedarius"
        )
        experiment_refusals = [
            refusal
            for refusal in camel.refusals
            if refusal.reason == "experiment_to_biological_sample_mapping_unavailable"
        ]
        self.assertEqual(len(experiment_refusals), 20)
        self.assertTrue(
            all(
                "sequencing experiment" in refusal.detail
                for refusal in experiment_refusals
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
                "site_curated": 1043,
                "sample_context_blocked": 402,
                "nordic_lead_site_curated": 5,
            },
        )
        self.assertTrue(
            all(sample.inclusion_note.strip() for sample in blocked_context)
        )
        self.assertEqual(
            sum(sample.locality is not None for sample in blocked_context),
            318,
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
                locality.locality.strip()
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
        self.assertTrue(
            any(
                refusal.reason == "locality_has_no_admitted_sample_identity"
                and refusal.source_token.startswith("SRP073444:")
                for refusal in camel.refusals
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
                    "archaeological_context",
                    "archaeological_context_date",
                    "sample_approximate_or_modeled",
                ),
                "Trelleborg": (
                    1000,
                    1000,
                    "archaeological_context",
                    "archaeological_context_date",
                    "sample_approximate_or_modeled",
                ),
            },
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
            {name: locality.dating_basis for name, locality in localities.items()},
            {
                "Hjørring, Tofte Bæk": "radiocarbon",
                "Lundby I": "mitochondrial_phylogenetic_model",
                "Nevishög": "radiocarbon",
                "Skåne": "radiocarbon",
            },
        )
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

    def test_source_mean_must_be_inside_its_canonical_interval(self) -> None:
        chronology = AdnaChronology(
            original_text="100-200 BP",
            time_start_bp=100,
            time_end_bp=200,
            time_mean_bp=150,
            dating_basis="radiocarbon",
        )

        with self.assertRaisesRegex(ValueError, "must lie inside"):
            _chronology_with_source_mean(chronology, 201)
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            _chronology_with_source_mean(chronology, True)
