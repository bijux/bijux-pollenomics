"""Bind the actual two-owner public reports without promoting checker or scientific roles."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.neotoma_lake import (
    transport as subject,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)


def owners() -> list[JsonObject]:
    return [
        {
            "owner_id": publication["owner_id"],
            "role": "retained_source",
            "paths": [name],
            "producer_paths": [],
            "producer_inputs": [],
        }
        for name, publication in subject.PUBLICATIONS.items()
    ]


def entries() -> dict[str, InventoryEntry]:
    return {
        name: InventoryEntry(
            path=name.removeprefix("docs/report/"),
            kind="file",
            sha256=publication["sha256"],
            size=publication["bytes"],
            canonical_sha256=publication["sha256"],
        )
        for name, publication in subject.PUBLICATIONS.items()
    }


class TransportControls(unittest.TestCase):
    def test_complete_actual_capsule_and_two_distinct_source_roles(self) -> None:
        got, evidence = subject.validated_neotoma_lake_capture(
            ROOT, entries(), owners()
        )
        self.assertEqual(len(got), 2)
        self.assertEqual(evidence["original_lake_sites"], 54)
        self.assertEqual(evidence["current_prerequisite_source_sites"], 163)
        self.assertIs(evidence["independent_pollen_eligibility_recomputed"], False)
        self.assertIs(evidence["whole_current_source_equivalence_claimed"], False)

    def test_owner_role_partition_and_overlap_refusals(self) -> None:
        original = owners()
        subject.validate_owners(original)
        for case in (
            "missing",
            "duplicate",
            "overlap",
            "executable",
            "extra_path",
            "source_reexecution",
        ):
            rows = deepcopy(original)
            if case == "missing":
                rows.pop()
            elif case == "duplicate":
                rows.append(deepcopy(rows[0]))
            elif case == "overlap":
                rows.append({"owner_id": "other", "paths": rows[0]["paths"]})
            elif case == "executable":
                rows[0]["role"] = "executable"
            elif case == "extra_path":
                rows[0]["paths"] = [
                    next(iter(subject.PUBLICATIONS)),
                    "docs/report/unqualified.json",
                ]
            else:
                rows[0]["producer_paths"] = ["invented-producer.py"]
            with self.assertRaises(ReportRebuildError):
                subject.validate_owners(rows)
