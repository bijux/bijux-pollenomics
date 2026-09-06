from __future__ import annotations

import copy
import unittest
from typing import cast

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)

from tests.support.neotoma import download_row


class NeotomaDiagnosticIdentityTests(unittest.TestCase):
    def test_conflict_resolution_is_invariant_to_source_order(self) -> None:
        first = download_row()
        second = copy.deepcopy(first)
        second_site = cast(dict[str, object], second["site"])
        second_site["sitename"] = "Conflicting source spelling"

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
        conflicts = cast(list[dict[str, object]], forward["conflicts"])
        self.assertEqual(len(conflicts), 2)
        self.assertEqual(
            len({cast(str, conflict["conflict_id"]) for conflict in conflicts}),
            2,
        )
        site_conflict = next(
            conflict
            for conflict in conflicts
            if conflict["conflict_kind"] == "site_payload_conflict"
        )
        detail = cast(dict[str, object], site_conflict["detail"])
        self.assertEqual(detail["resolution"], "canonical_minimum")
        self.assertEqual(len(cast(list[object], detail["variants"])), 2)

    def test_repeated_orphan_events_receive_unique_stable_ids(self) -> None:
        missing_identity = {"site": {"sitename": "Missing identity"}}

        payload = build_neotoma_relational_snapshot(
            [missing_identity, copy.deepcopy(missing_identity)],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        orphans = cast(list[dict[str, object]], payload["orphans"])
        orphan_ids = [cast(str, orphan["orphan_id"]) for orphan in orphans]
        self.assertEqual(len(orphan_ids), 2)
        self.assertEqual(len(set(orphan_ids)), 2)
        self.assertTrue(orphan_ids[1].endswith(":2"))


if __name__ == "__main__":
    unittest.main()
