"""Closed current aDNA evidence boundaries without production or sample parsing."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.adna.current_export import (
    WITNESS,
    checked,
    exact_tree,
    publisher_contract,
    validated_aadr_current_export_evidence,
)


class CurrentExportBoundaries(unittest.TestCase):
    def owners(self) -> list[dict[str, object]]:
        paths = []
        for country in ("denmark", "finland", "norway", "sweden"):
            paths.extend(
                [
                    f"docs/report/countries/{country}/README.md",
                    *[
                        f"docs/report/countries/{country}/{country}_aadr_v66_samples.{suffix}"
                        for suffix in ("csv", "geojson", "md")
                    ],
                ]
            )
        return [
            {"owner_id": "publisher", "role": "publisher_partition", "paths": paths}
        ]

    def test_existing_publisher_only(self) -> None:
        owners = self.owners()
        self.assertEqual(len(publisher_contract(owners)), 16)
        for value in ["retained_source", "generated_owner"]:
            owners[0]["role"] = value
            with self.assertRaises(ReportRebuildError):
                publisher_contract(owners)
        owners = self.owners()
        owners.append(dict(owners[0]))
        with self.assertRaises(ReportRebuildError):
            publisher_contract(owners)

    def test_optional_absence_and_partial_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            self.assertIsNone(validated_aadr_current_export_evidence(root, []))
            path = root / WITNESS
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}")
            with self.assertRaises(ReportRebuildError):
                validated_aadr_current_export_evidence(root, self.owners())

    def test_total_regular_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            (root / "payloads").mkdir()
            (root / "capture.json").write_bytes(b"{}")
            (root / "payloads/a").write_bytes(b"bytes")
            members = {"capture.json", "payloads/a"}
            exact_tree(root, members)
            (root / "extra").mkdir()
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, members)
            (root / "extra").rmdir()
            fifo = root / "payloads/fifo"
            os.mkfifo(fifo)
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, members)
            fifo.unlink()
            (root / "payloads/alias").symlink_to(root / "payloads/a")
            with self.assertRaises(ReportRebuildError):
                exact_tree(root, members)

    def test_exact_bytes_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            path = root / "metadata.json"
            path.write_bytes(b"{}")
            checksum = hashlib.sha256(b"{}").hexdigest()
            self.assertEqual(checked(root, "metadata.json", checksum), b"{}")
            path.write_bytes(b"{ }")
            with self.assertRaises(ReportRebuildError):
                checked(root, "metadata.json", checksum)
            alias = root / "alias"
            alias.symlink_to(path)
            with self.assertRaises(ReportRebuildError):
                checked(root, "alias", checksum)
