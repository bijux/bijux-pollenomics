from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    normalize_neotoma_rows,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _governed_neotoma_sites,
)


class NeotomaCountryProjectionTests(unittest.TestCase):
    def test_governed_map_projection_excludes_unassigned_relational_sites(self) -> None:
        sites = {
            "neotoma:site:assigned": {
                "country_code": "SE",
                "country_decision_status": "assigned",
            },
            "neotoma:site:review": {
                "country_code": "UNASSIGNED",
                "country_decision_status": "review",
            },
            "neotoma:site:conflict": {
                "country_code": "NO",
                "country_decision_status": "review",
            },
        }

        governed = _governed_neotoma_sites(sites)

        self.assertEqual(list(governed), ["neotoma:site:assigned"])

    def test_normalize_neotoma_rows_refuses_coastal_proximity_without_snapping(
        self,
    ) -> None:
        country_boundaries: dict[str, dict[str, object]] = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 60.0],
                                    [13.0, 60.0],
                                    [13.0, 63.0],
                                    [10.0, 63.0],
                                    [10.0, 60.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 1,
                "sitename": "Coastal site",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.05,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 10, "datasettype": "pollen"}],
                    }
                ],
            },
            {
                "siteid": 2,
                "sitename": "Too far away",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.5,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 20, "datasettype": "pollen"}],
                    }
                ],
            },
        ]

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        self.assertEqual(records, [])

    def test_normalize_neotoma_rows_refuses_raw_country_conflicts(self) -> None:
        country_boundaries: dict[str, dict[str, object]] = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        }
                    }
                ]
            },
            "Norway": {"features": []},
        }
        rows = [
            {
                "siteid": 10,
                "sitename": "Conflicting source country",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "geopolitical": [{"country": "Norway"}],
                "collectionunits": [],
            }
        ]

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        self.assertEqual(records, [])

    def test_normalize_neotoma_rows_surfaces_country_decision_provenance(self) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 10,
                "sitename": "Governed country",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "collectionunits": [],
            }
        ]

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        popup = dict(records[0].popup_rows)
        self.assertEqual(popup["Country decision"], "assigned")
        self.assertEqual(popup["Country method"], "strict_boundary_containment")
        self.assertEqual(
            popup["Boundary version"], "content-addressed-boundary-collection"
        )
        self.assertRegex(popup["Boundary digest"], r"^sha256:[0-9a-f]{64}$")

    def test_normalize_neotoma_rows_respects_an_empty_authoritative_decision_set(
        self,
    ) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 10,
                "sitename": "Unreviewed country",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "collectionunits": [],
            }
        ]

        records = normalize_neotoma_rows(
            rows,
            (4.0, 54.0, 35.0, 72.0),
            country_boundaries,
            country_decisions={},
        )

        self.assertEqual(records, [])
