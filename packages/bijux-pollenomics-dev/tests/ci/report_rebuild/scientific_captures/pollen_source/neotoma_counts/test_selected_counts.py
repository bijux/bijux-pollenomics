"""Guard current selected counts without promoting historical mass or manifest custody."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_counts.selected_counts import (
    CAPTURE,
    ORIGINAL_COUNT_CRITERION,
    OWNERS,
    WITNESS,
    exact_tree,
    ownership,
    physical,
    validated_neotoma_selected_count_evidence,
)


class SelectedCountBoundaries(unittest.TestCase):
    def owners(self) -> list[JsonObject]:
        return [
            {
                "owner_id": name,
                "role": "unresolved",
                "verification": ORIGINAL_COUNT_CRITERION,
                "paths": [path],
                "producer_paths": [],
                "producer_inputs": [],
            }
            for name, path in OWNERS.items()
        ]

    def test_exact_two_current_count_owners(self) -> None:
        rows = self.owners()
        ownership(rows)
        for key, value in [
            ("role", "retained_source"),
            ("verification", "Current rows alone suffice"),
            ("producer_paths", ["source.py"]),
            ("producer_inputs", ["private.json"]),
            ("paths", ["docs/report/historical-manifest.json"]),
        ]:
            changed = deepcopy(rows)
            changed[0][key] = value
            with self.assertRaises(ReportRebuildError):
                ownership(changed)
        with self.assertRaises(ReportRebuildError):
            ownership(rows + [dict(rows[0])])
        with self.assertRaises(ReportRebuildError):
            ownership(rows[:1])

    def test_other_owner_overlap_and_disjoint_historical_sibling(self) -> None:
        rows = self.owners()
        sibling: JsonObject = {
            "owner_id": "source-relations/neotoma/abbo-core-identity/custody-manifest",
            "role": "unresolved",
            "paths": [
                "docs/report/source-relations/neotoma/abbo-core-identity/manifest.json"
            ],
            "producer_paths": [],
            "producer_inputs": [],
        }
        ownership(rows + [sibling])
        sibling["paths"] = [next(iter(OWNERS.values()))]
        with self.assertRaises(ReportRebuildError):
            ownership(rows + [sibling])

    def test_optional_absence_and_partial_owner_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            self.assertEqual(
                validated_neotoma_selected_count_evidence(root, {}, []), {}
            )
            self.assertEqual(
                validated_neotoma_selected_count_evidence(root, {}, self.owners()), {}
            )
            with self.assertRaises(ReportRebuildError):
                validated_neotoma_selected_count_evidence(root, {}, self.owners()[:1])
            path = root / CAPTURE
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}")
            with self.assertRaises(ReportRebuildError):
                validated_neotoma_selected_count_evidence(root, {}, [])

    def test_published_witness_requires_capture(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            witness = root / WITNESS
            witness.parent.mkdir(parents=True)
            witness.write_bytes(b"{}")
            with self.assertRaises(ReportRebuildError):
                validated_neotoma_selected_count_evidence(root, {}, self.owners())
            witness.unlink()
            witness.symlink_to(root / "missing-witness")
            with self.assertRaises(ReportRebuildError):
                validated_neotoma_selected_count_evidence(root, {}, self.owners())
            witness.unlink()
            os.mkfifo(witness)
            with self.assertRaises(ReportRebuildError):
                validated_neotoma_selected_count_evidence(root, {}, self.owners())
            witness.unlink()
            self.assertEqual(
                validated_neotoma_selected_count_evidence(root, {}, self.owners()), {}
            )

    def test_exact_total_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            (root / "payloads").mkdir()
            (root / "capture.json").write_bytes(b"{}")
            (root / "payloads/item").write_bytes(b"x")
            files = {"payloads/item"}
            exact_tree(root, files)
            (root / "extra").mkdir()
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, files)
            (root / "extra").rmdir()
            os.mkfifo(root / "payloads/fifo")
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, files)
            (root / "payloads/fifo").unlink()
            (root / "payloads/alias").symlink_to(root / "payloads/item")
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, files)
            with self.assertRaises(ReportRebuildError):
                physical(root, "payloads/alias")
            self.assertEqual(
                hashlib.sha256(
                    physical(root, "payloads/item").read_bytes()
                ).hexdigest(),
                hashlib.sha256(b"x").hexdigest(),
            )
