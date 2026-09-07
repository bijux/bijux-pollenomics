"""AADR context-point projection coverage."""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import cast

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.reporting.context import build_aadr_point_layer


class AadrLayerTests(unittest.TestCase):
    def test_build_aadr_point_layer_includes_release_version_in_label(self) -> None:
        layer = build_aadr_point_layer(samples=(), version="v66")

        self.assertEqual(layer["label"], "AADR-v66 aDNA samples")

    def test_build_aadr_point_layer_surfaces_provenance_rich_popup_rows(self) -> None:
        sample = AdnaSampleRecord(
            identity=AdnaSampleIdentity(
                namespace="homo_sapiens:aadr_genetic_id",
                stable_token="SE1",
                accession_lineage=("species:Homo sapiens", "dataset:ho"),
            ),
            locality_identity=AdnaLocalityIdentity(
                namespace="homo_sapiens:locality",
                stable_token="homo_sapiens:aadr:uppsala",
                locality_text="Uppsala",
                political_entity="Sweden",
                source_anchor_tokens=("SE1",),
            ),
            species_latin_name="Homo sapiens",
            species_common_name="human",
            source_family="AADR",
            source_release="v66",
            record_modality="metadata_only",
            review_strength="curated_release_metadata",
            provenance_quality="release_manifest_pinned",
            master_id="SE1",
            group_id="Sweden_Group",
            locality="Uppsala",
            political_entity="Sweden",
            coordinates=AdnaCoordinate(
                latitude=59.8586,
                longitude=17.6389,
                latitude_text="59.8586",
                longitude_text="17.6389",
                confidence="exact",
            ),
            publication="PaperA",
            year_first_published="2022",
            full_date="500 BCE",
            chronology=AdnaChronology(
                original_text="500 BCE",
                time_start_bp=2200,
                time_end_bp=2700,
                time_mean_bp=2450,
                dating_basis="bp_mean_and_stddev",
                evidence_class="direct_numeric_sample_date",
                precision_posture="sample_precise_interval",
            ),
            data_type="HO",
            molecular_sex="F",
            datasets=("ho",),
        )
        layer = build_aadr_point_layer(samples=(sample,), version="v66")

        feature = cast(list[dict[str, object]], layer["features"])[0]
        popup = {
            row["label"]: row["value"]
            for row in cast(list[dict[str, str]], feature["popup_rows"])
        }

        self.assertEqual(layer["atlas_layer_key"], "homo_sapiens_direct")
        self.assertEqual(layer["contribution_role"], "direct")
        self.assertEqual(
            feature["record_id"], "homo_sapiens:aadr_genetic_id:SE1"
        )
        self.assertEqual(feature["species_latin_name"], "Homo sapiens")
        self.assertEqual(feature["evidence_role"], "direct")
        self.assertEqual(popup["Source release"], "v66")
        self.assertEqual(popup["Record modality"], "metadata_only")
        self.assertEqual(popup["Coordinate confidence"], "exact")
        self.assertEqual(popup["Dating basis"], "bp_mean_and_stddev")
        self.assertEqual(
            cast(dict[str, object], feature["temporal_semantics"])[
                "comparability_posture"
            ],
            "numeric_interval",
        )

        refused_sample = replace(
            sample,
            chronology=AdnaChronology(
                original_text="historical",
                time_start_bp=None,
                time_end_bp=None,
                time_mean_bp=None,
                date_stddev_bp="89",
                source_mean_bp_text="146",
                dating_basis="bp_mean_and_stddev",
                evidence_class="direct_numeric_sample_date",
                precision_posture="sample_precise_interval",
                refusal_reason_code="negative_bp",
            ),
        )
        refused_layer = build_aadr_point_layer(samples=(refused_sample,), version="v66")
        refused_feature = cast(list[dict[str, object]], refused_layer["features"])[0]
        refused_semantics = cast(
            dict[str, object], refused_feature["temporal_semantics"]
        )
        self.assertIsNone(refused_feature["time_start_bp"])
        self.assertIsNone(refused_feature["time_end_bp"])
        self.assertIsNone(refused_feature["time_mean_bp"])
        self.assertEqual(refused_semantics["comparability_posture"], "refused")
        self.assertEqual(refused_semantics["refusal_reason_code"], "negative_bp")


if __name__ == "__main__":
    unittest.main()
