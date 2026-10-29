"""The public capsule validates current evidence without admitting unresolved source ownership."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_publication import (
    transport as subject,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)


def owners() -> list[JsonObject]:
    return [deepcopy(subject.ORIGINAL_OWNER)]


def entries() -> dict[str, InventoryEntry]:
    return {
        name: InventoryEntry(
            path=name.removeprefix("docs/report/"),
            kind="file",
            sha256=row["sha256"],
            size=row["bytes"],
            canonical_sha256=row["sha256"],
        )
        for name, row in subject.PRODUCTS.items()
    }


class TransportControls(unittest.TestCase):
    def test_complete_capsule_and_two_products(self) -> None:
        got, evidence = subject.validated_neotoma_publication_capture(
            ROOT, entries(), owners()
        )
        self.assertEqual(len(got), 0)
        self.assertEqual(evidence["original_whole_exit"], 1)
        self.assertEqual(evidence["original_tracked_checker_exits"], [2, 2])
        self.assertIs(
            evidence["original_HTTP_rights_citation_selection_human_or_LRA_admission"],
            False,
        )

    def test_exact_owner_partition_refusals(self) -> None:
        for case in (
            "missing",
            "duplicate",
            "overlap",
            "producer",
            "third_path",
            "unresolved",
        ):
            rows = deepcopy(owners())
            if case == "missing":
                rows = []
            elif case == "duplicate":
                rows.append(deepcopy(rows[0]))
            elif case == "overlap":
                rows.append({"owner_id": "foreign", "paths": rows[0]["paths"]})
            elif case == "producer":
                rows[0]["producer_paths"] = ["invented.py"]
            elif case == "third_path":
                rows[0]["paths"] = [
                    *sorted(subject.PRODUCTS),
                    "docs/report/never-produced.json",
                ]
            else:
                rows[0]["role"] = "retained_source"
            with self.subTest(case=case), self.assertRaises(ReportRebuildError):
                subject.validate_owner(rows)
