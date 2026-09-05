from __future__ import annotations

from bijux_pollenomics.reporting.geography import build_published_geography_plan
from bijux_pollenomics.reporting.map_document.state import build_map_document_state
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

from .support import MapPublicationTestCase


class ScopeAndTimeStateTests(MapPublicationTestCase):
    def test_scope_policies_keep_distinct_bounds_and_basemaps(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway", "Germany"))
        world_policy = resolve_map_scope_policy(plan.world_scope)
        europe_plus_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "europe_plus")
        )
        nordic_policy = resolve_map_scope_policy(
            next(scope for scope in plan.regional_scopes if scope.key == "nordic")
        )

        self.assertEqual(world_policy.default_basemap, "voyager")
        self.assertEqual(europe_plus_policy.default_basemap, "light")
        self.assertEqual(nordic_policy.default_basemap, "voyager")
        self.assertLess(
            world_policy.minimum_bounds[0][1], europe_plus_policy.minimum_bounds[0][1]
        )
        self.assertLess(
            europe_plus_policy.minimum_bounds[0][1], nordic_policy.minimum_bounds[0][1]
        )

    def test_map_document_state_uses_scope_floor_bounds(self) -> None:
        plan = build_published_geography_plan(("Sweden", "Norway"))
        world_policy = resolve_map_scope_policy(plan.world_scope)
        state = build_map_document_state(
            policy=world_policy,
            point_layers=[
                {
                    "features": [
                        {"latitude": 59.33, "longitude": 18.06},
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertEqual(state.initial_diameter_km, world_policy.initial_diameter_km)
        self.assertLessEqual(state.bounds[0][1], world_policy.minimum_bounds[0][1])
        self.assertGreaterEqual(state.bounds[1][1], world_policy.minimum_bounds[1][1])

    def test_map_time_state_rejects_non_numeric_values_and_preserves_zero(self) -> None:
        plan = build_published_geography_plan(("Sweden",))
        policy = resolve_map_scope_policy(plan.world_scope)
        state = build_map_document_state(
            policy=policy,
            point_layers=[
                {
                    "features": [
                        {
                            "latitude": 59.33,
                            "longitude": 18.06,
                            "time_start_bp": None,
                            "time_end_bp": "",
                            "time_mean_bp": False,
                            "time_year_bp": "nan",
                        },
                        {
                            "latitude": 55.60,
                            "longitude": 13.00,
                            "time_start_bp": 0,
                            "time_end_bp": 100,
                        },
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertTrue(state.has_time_data)
        self.assertEqual(state.time_min_bp, 0)
        self.assertEqual(state.time_max_bp, 100)

    def test_map_time_state_refuses_partial_or_reversed_intervals(self) -> None:
        policy = resolve_map_scope_policy(
            build_published_geography_plan(("Sweden",)).world_scope
        )
        state = build_map_document_state(
            policy=policy,
            point_layers=[
                {
                    "features": [
                        {"time_start_bp": 0, "time_mean_bp": 25},
                        {"time_start_bp": 100, "time_end_bp": 50},
                    ]
                }
            ],
            polygon_layers=[],
        )

        self.assertFalse(state.has_time_data)
        self.assertEqual((state.time_min_bp, state.time_max_bp), (0, 0))
