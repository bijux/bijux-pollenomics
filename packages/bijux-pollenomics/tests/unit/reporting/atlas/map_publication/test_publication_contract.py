from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_publication import (
    _serialize_layer_contract_row,
    build_map_point_traceability,
    build_map_publication_contract,
    render_map_point_traceability_markdown,
    resolve_map_scope_policy,
)
from bijux_pollenomics.reporting.models import MultiCountryMapReport

from .support import MapPublicationTestCase


class PublicationContractTests(MapPublicationTestCase):
    @staticmethod
    def _animal_chronology_layer() -> dict[str, object]:
        return {
            "key": "animal-source-chronology-equus-caballus",
            "label": "Horse source-sample chronology",
            "source_name": "Governed animal project sample chronology",
            "coverage_label": "Exact project and sample joins.",
            "count": 0,
            "features": [],
            "group": "animal-chronology-context",
            "semantic_role": "animal_source_chronology_context",
            "contribution_role": "display_only",
            "default_enabled": False,
            "applies_country_filter": True,
            "applies_time_filter": True,
            "candidate_ranking_eligible": False,
            "scientific_classification_eligible": False,
            "scientific_selection_enabled": False,
            "propagation_status": "refused",
            "propagation_reason_code": "display_only_source_chronology",
            "edge_count": 0,
            "circle_enabled": False,
            "project_species_latin_name": "Equus caballus",
            "project_species_common_name": "horse",
            "species_attribution_basis": "governed_project_registry",
        }

    def test_layer_contract_preserves_zero_and_derives_only_absent_legacy_count(
        self,
    ) -> None:
        policy = resolve_map_scope_policy(None)
        zero = _serialize_layer_contract_row(
            {"key": "empty", "count": 0, "features": []},
            policy=policy,
        )
        legacy = _serialize_layer_contract_row(
            {"key": "legacy", "features": [{}, {}]},
            policy=policy,
        )

        self.assertEqual(zero["count"], 0)
        self.assertEqual(legacy["count"], 2)

    def test_point_traceability_normalizes_layer_metadata_without_data_loss(
        self,
    ) -> None:
        report = MultiCountryMapReport(
            title="Nordic Evidence Surface",
            slug="nordic",
            version="v66",
            generated_on="2026-05-09",
            countries=("Sweden", "Norway"),
            country_sample_counts={"Sweden": 1, "Norway": 1},
            total_unique_samples=2,
            output_dir=Path("/tmp/docs/report/regions/nordic"),
            scope_key="nordic",
            scope_label="Nordic",
            scope_kind="region",
            parent_scope_key="europe_plus",
        )
        payload = build_map_point_traceability(
            report=report,
            point_layers=[
                {
                    "key": "zebra",
                    "label": "Zebra layer",
                    "group": "animal-evidence",
                    "source_name": "Example source",
                    "traceability_artifact": "zebra.json",
                    "traceability_reference": "https://example.test/zebra",
                    "features": [
                        {
                            "evidence_row_id": "zebra:1",
                            "title": "Zebra one",
                            "country": "Sweden",
                            "source_url": "https://example.test/zebra/1",
                            "species_latin_name": "Equus quagga",
                            "animal_scope": "comparator",
                            "coordinate_confidence": "exact",
                        }
                    ],
                },
                {
                    "key": "aadr",
                    "label": "Human samples",
                    "source_name": "AADR",
                    "features": [
                        {"title": "Sample one", "country": "Norway"},
                        {"title": "Sample two", "country": "Sweden"},
                    ],
                },
            ],
        )

        self.assertEqual(payload["schema_version"], "map-point-traceability.v2")
        self.assertEqual(payload["scope_key"], "nordic")
        self.assertEqual(payload["row_count"], 3)
        self.assertEqual(payload["layer_counts"], {"aadr": 2, "zebra": 1})
        layers = payload["layers"]
        self.assertIsInstance(layers, list)
        self.assertEqual([layer["layer_key"] for layer in layers], ["aadr", "zebra"])
        self.assertEqual(layers[0]["row_count"], 2)
        self.assertEqual(
            layers[0]["field_counts"],
            {
                "title": 2,
                "country": 2,
                "source_url": 0,
                "species_latin_name": 0,
                "animal_scope": 0,
                "coordinate_confidence": 0,
            },
        )
        self.assertNotIn("source_url", layers[0]["records"][0])
        self.assertEqual(layers[1]["records"][0]["record_id"], "zebra:1")
        self.assertNotIn("layer_key", layers[1]["records"][0])
        self.assertNotIn("scope_key", layers[1]["records"][0])

        markdown = render_map_point_traceability_markdown(payload)
        self.assertIn("Visible point rows: `3`", markdown)
        self.assertIn("| Zebra layer | zebra:1 | Sweden | zebra.json |", markdown)

        with self.assertRaisesRegex(ValueError, "layer key is duplicated"):
            build_map_point_traceability(
                report=report,
                point_layers=[
                    {"key": "aadr", "features": []},
                    {"key": "aadr", "features": []},
                ],
            )

    def test_layer_contract_refuses_malformed_or_drifting_declared_count(
        self,
    ) -> None:
        policy = resolve_map_scope_policy(None)
        for value in (None, "", "0", False, True, -1, 0.0):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "nonnegative integer"),
            ):
                _serialize_layer_contract_row(
                    {"key": "invalid", "count": value},
                    policy=policy,
                )
        with self.assertRaisesRegex(ValueError, "does not match its features"):
            _serialize_layer_contract_row(
                {"key": "drift", "count": 2, "features": [{}]},
                policy=policy,
            )

    def test_map_publication_contract_distinguishes_layer_roles(self) -> None:
        report = MultiCountryMapReport(
            title="Nordic Evidence Surface",
            slug="nordic",
            version="v66",
            generated_on="2026-05-09",
            countries=("Sweden", "Norway"),
            country_sample_counts={"Sweden": 1, "Norway": 1},
            total_unique_samples=2,
            output_dir=Path("/tmp/docs/report/regions/nordic"),
            scope_key="nordic",
            scope_label="Nordic",
            scope_kind="region",
            parent_scope_key="europe_plus",
        )
        policy = resolve_map_scope_policy(
            next(
                scope
                for scope in build_published_geography_plan(
                    ("Sweden", "Norway")
                ).regional_scopes
                if scope.key == "nordic"
            )
        )
        bundle_paths = build_atlas_bundle_paths(Path("/tmp/nordic"), "nordic", "v66")
        contract = build_map_publication_contract(
            report=report,
            policy=policy,
            point_layers=[
                {
                    "key": "aadr",
                    "label": "AADR-v66 aDNA samples",
                    "source_name": "Allen Ancient DNA Resource",
                    "coverage_label": "Country assignment follows the AADR political entity field.",
                    "count": 2,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": True,
                },
                {
                    "key": "landclim-sites",
                    "label": "LandClim pollen sequences",
                    "source_name": "LandClim",
                    "coverage_label": "Pollen sequences staged from the LandClim normalization bundle.",
                    "count": 1,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": False,
                },
            ],
            polygon_layers=[
                {
                    "key": "country-boundaries",
                    "label": "Country boundaries",
                    "source_name": "Natural Earth country boundaries",
                    "coverage_label": "Published country outlines used for framing and scope-aware map filtering.",
                    "count": 2,
                    "default_enabled": True,
                    "applies_country_filter": True,
                    "applies_time_filter": False,
                }
            ],
            countries=report.countries,
            map_html_name=bundle_paths.map_html_path.name,
            summary_json_name=bundle_paths.summary_json_path.name,
            traceability_json_name=bundle_paths.map_point_traceability_json_path.name,
        )

        self.assertEqual(
            contract["role_counts"]["shared_world_scale_layer"],  # type: ignore[index]
            1,
        )
        self.assertEqual(
            contract["role_counts"]["region_filtered_layer"],  # type: ignore[index]
            1,
        )
        self.assertEqual(
            contract["role_counts"]["scope_specific_overlay"],  # type: ignore[index]
            1,
        )

    def test_animal_chronology_is_shared_and_never_described_as_withheld(self) -> None:
        for scope_key in ("world", "europe_plus", "nordic"):
            with self.subTest(scope_key=scope_key):
                row = _serialize_layer_contract_row(
                    self._animal_chronology_layer(),
                    policy=resolve_map_scope_policy(
                        build_published_geography_plan(("Sweden",)).world_scope
                    )
                    if scope_key == "world"
                    else resolve_map_scope_policy(
                        next(
                            scope
                            for scope in build_published_geography_plan(
                                ("Sweden",)
                            ).regional_scopes
                            if scope.key == scope_key
                        )
                    ),
                )

                self.assertEqual(row["publication_role"], "shared_world_scale_layer")
                self.assertNotIn("withheld", str(row["scope_caveat"]).casefold())
                self.assertIn("display-only source chronology", row["scope_caveat"])
                self.assertEqual(row["group"], "animal-chronology-context")
                self.assertEqual(
                    row["semantic_role"], "animal_source_chronology_context"
                )
                self.assertIs(row["default_enabled"], False)
                self.assertIs(row["candidate_ranking_eligible"], False)
                self.assertIs(row["scientific_classification_eligible"], False)
                self.assertIs(row["scientific_selection_enabled"], False)
                self.assertEqual(row["propagation_status"], "refused")
                self.assertEqual(
                    row["propagation_reason_code"],
                    "display_only_source_chronology",
                )
                self.assertEqual(row["edge_count"], 0)
                self.assertIs(row["circle_enabled"], False)
                self.assertEqual(row["project_species_latin_name"], "Equus caballus")
                self.assertEqual(row["project_species_common_name"], "horse")
                self.assertEqual(
                    row["species_attribution_basis"], "governed_project_registry"
                )

    def test_animal_chronology_publication_posture_fails_closed(self) -> None:
        policy = resolve_map_scope_policy(None)
        expected_fields = (
            "group",
            "semantic_role",
            "contribution_role",
            "default_enabled",
            "applies_country_filter",
            "applies_time_filter",
            "candidate_ranking_eligible",
            "scientific_classification_eligible",
            "scientific_selection_enabled",
            "propagation_status",
            "propagation_reason_code",
            "edge_count",
            "circle_enabled",
        )
        for field in expected_fields:
            layer = self._animal_chronology_layer()
            layer.pop(field)
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(
                    ValueError, "animal source chronology context posture differs"
                ),
            ):
                _serialize_layer_contract_row(layer, policy=policy)

        contradictory = self._animal_chronology_layer()
        contradictory["semantic_role"] = "accepted_scientific_classification"
        with self.assertRaisesRegex(ValueError, "semantic_role"):
            _serialize_layer_contract_row(contradictory, policy=policy)

    def test_animal_chronology_feature_posture_and_identity_fail_closed(self) -> None:
        policy = resolve_map_scope_policy(None)
        feature = {
            "feature_id": "animal-sample:PRJEB31613:horse-1",
            "project_accession": "PRJEB31613",
            "repo_stable_sample_id": "horse-1",
            "project_species_latin_name": "Equus caballus",
            "project_species_common_name": "horse",
            "species_attribution_basis": "governed_project_registry",
            "semantic_role": "animal_source_chronology_context",
            "contribution_role": "display_only",
            "candidate_ranking_eligible": False,
            "scientific_classification_eligible": False,
            "scientific_selection_enabled": False,
            "propagation_status": "refused",
            "propagation_reason_code": "display_only_source_chronology",
            "edge_count": 0,
        }
        layer = self._animal_chronology_layer()
        layer.update({"count": 1, "features": [feature]})
        row = _serialize_layer_contract_row(layer, policy=policy)
        self.assertEqual(row["count"], 1)

        for field in (
            "semantic_role",
            "contribution_role",
            "candidate_ranking_eligible",
            "scientific_classification_eligible",
            "scientific_selection_enabled",
            "propagation_status",
            "propagation_reason_code",
            "edge_count",
        ):
            invalid = self._animal_chronology_layer()
            invalid_feature = dict(feature)
            invalid_feature.pop(field)
            invalid.update({"count": 1, "features": [invalid_feature]})
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "feature posture differs"),
            ):
                _serialize_layer_contract_row(invalid, policy=policy)

        duplicate = self._animal_chronology_layer()
        duplicate.update({"count": 2, "features": [feature, dict(feature)]})
        with self.assertRaisesRegex(ValueError, "identity is duplicated"):
            _serialize_layer_contract_row(duplicate, policy=policy)

    def test_animal_chronology_forbids_accepted_taxonomy_aliases(self) -> None:
        policy = resolve_map_scope_policy(None)
        feature = {
            "feature_id": "animal-sample:PRJEB31613:horse-1",
            "project_accession": "PRJEB31613",
            "repo_stable_sample_id": "horse-1",
            "project_species_latin_name": "Equus caballus",
            "project_species_common_name": "horse",
            "species_attribution_basis": "governed_project_registry",
            "semantic_role": "animal_source_chronology_context",
            "contribution_role": "display_only",
            "candidate_ranking_eligible": False,
            "scientific_classification_eligible": False,
            "scientific_selection_enabled": False,
            "propagation_status": "refused",
            "propagation_reason_code": "display_only_source_chronology",
            "edge_count": 0,
        }
        forbidden = (
            "animal_scope",
            "classification_id",
            "classification_status",
            "scientific_signal_ids",
            "species_common_name",
            "species_latin_name",
            "taxon_alignment_status",
            "taxon_alignment_statuses",
        )
        for field in forbidden:
            layer = self._animal_chronology_layer()
            layer[field] = "forbidden"
            with (
                self.subTest(surface="layer", field=field),
                self.assertRaisesRegex(ValueError, "forbidden scientific fields"),
            ):
                _serialize_layer_contract_row(layer, policy=policy)
        for field in forbidden:
            layer = self._animal_chronology_layer()
            invalid_feature = dict(feature)
            invalid_feature[field] = "forbidden"
            layer.update({"count": 1, "features": [invalid_feature]})
            with (
                self.subTest(surface="feature", field=field),
                self.assertRaisesRegex(ValueError, "forbidden scientific fields"),
            ):
                _serialize_layer_contract_row(layer, policy=policy)
