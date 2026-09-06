from __future__ import annotations

import copy
import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)

from tests.support.neotoma import (
    download_row,
)


class NeotomaRelationalDeterminismTests(unittest.TestCase):
    def test_output_is_invariant_to_download_row_order(self) -> None:
        first = download_row(201)
        second = download_row(202)
        second["site"]["collectionunit"]["dataset"]["samples"][0]["sampleid"] = 9999
        second["site"]["collectionunit"]["dataset"]["samples"][0]["analysisunitid"] = (
            9302
        )

        forward = build_neotoma_relational_snapshot(
            [first, second],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )
        reverse = build_neotoma_relational_snapshot(
            [copy.deepcopy(second), copy.deepcopy(first)],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        self.assertEqual(forward, reverse)
