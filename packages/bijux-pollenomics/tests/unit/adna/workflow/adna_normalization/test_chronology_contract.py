from __future__ import annotations

from types import SimpleNamespace
from typing import cast
import unittest

from bijux_pollenomics.adna import AdnaChronology
from bijux_pollenomics.adna.projects.evidence.chronology.models import (
    AdnaProjectSampleChronologyRow,
)
from bijux_pollenomics.adna.projects.registry.samples import AdnaCuratedSampleRow
from bijux_pollenomics.adna.workflow.normalization.samples import (
    _chronology_with_source_mean,
)

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationChronologyTests(unittest.TestCase):
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
                cast(list[AdnaCuratedSampleRow], rows),
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
            _aggregate_locality_precision_posture(
                cast(list[AdnaProjectSampleChronologyRow], rows), chronology
            ),
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
            sample_rows=cast(tuple[AdnaCuratedSampleRow, ...], sample_rows),
            chronology_lookup=cast(
                dict[str, AdnaProjectSampleChronologyRow], chronology_lookup
            ),
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
