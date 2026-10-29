"""Closed physical membership refuses unlisted files, links, special entries and identity coercion."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_publication import (
    members as subject,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)
ARTIFACTS = ROOT / "artifacts/science/neotoma-publication-member-controls"


class MemberControls(unittest.TestCase):
    def test_actual_directories_and_special_entry_refusals(self) -> None:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        for case in (
            "positive",
            "extra",
            "missing",
            "alias",
            "directory_alias",
            "FIFO",
            "bool_size",
            "bytecode",
            "escape",
        ):
            with tempfile.TemporaryDirectory(dir=ARTIFACTS) as folder:
                root = Path(folder)
                (root / "source").mkdir()
                (root / "capture.json").write_text("{}")
                target = root / "source/entry.py"
                target.write_bytes(b"owned source\n")
                members = {
                    "source/entry.py": {
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "bytes": target.stat().st_size,
                    }
                }
                if case == "extra":
                    (root / "unknown").write_text("extra")
                elif case == "missing":
                    target.unlink()
                elif case == "alias":
                    (root / "alias").symlink_to(target)
                elif case == "directory_alias":
                    (root / "alias").symlink_to(
                        root / "source", target_is_directory=True
                    )
                elif case == "FIFO":
                    os.mkfifo(root / "pipe")
                elif case == "bool_size":
                    members["source/entry.py"]["bytes"] = True
                elif case == "bytecode":
                    (root / "source/entry.pyc").write_bytes(b"x")
                elif case == "escape":
                    members["../escape"] = {"sha256": "0" * 64, "bytes": 0}
                if case == "positive":
                    subject.validate_members(root, members)
                else:
                    with self.subTest(case=case), self.assertRaises(ReportRebuildError):
                        subject.validate_members(root, members)

    def test_complete_ordered_catalog_and_unreviewed_omission_refusals(self) -> None:
        pin: dict[str, Any] = {
            "path": "/repository/packages/host/src/source.py",
            "sha256": "0" * 64,
            "bytes": 7,
        }
        row = {
            **pin,
            "original_index": 0,
            "retention_role": "retained_original_public_source",
            "retained_member": "source/source.py",
        }
        original_roles = {
            pin["path"]: {
                **pin,
                "retained_member": "source/source.py",
                "retention_role": "retained_public_first_party_source_or_resource",
            }
        }
        members = {"source/source.py": {"sha256": "0" * 64, "bytes": 7}}

        def validate(rows: list[dict[str, Any]]) -> None:
            subject.validate_catalog(
                rows,
                [pin],
                members,
                original_roles=original_roles,
                runtime_paths=set(),
                repository="/repository",
                retained_aliases={},
            )

        validate([row])
        for case in (
            "missing",
            "index_bool",
            "size_bool",
            "private",
            "runtime",
            "bytecode",
            "member",
            "unknown",
        ):
            rows = [deepcopy(row)]
            if case == "missing":
                rows = []
            elif case == "index_bool":
                rows[0]["original_index"] = False
            elif case == "size_bool":
                rows[0]["bytes"] = True
            elif case in ("private", "runtime", "bytecode"):
                rows[0]["retention_role"] = {
                    "private": "private_source_identity_only",
                    "runtime": "runtime_dependency_identity_only",
                    "bytecode": "bytecode_identity_only",
                }[case]
                rows[0]["retained_member"] = None
            elif case == "member":
                rows[0]["retained_member"] = "source/unreviewed.py"
            else:
                rows[0]["retention_role"] = "unknown"
            with self.subTest(case=case), self.assertRaises(ReportRebuildError):
                validate(rows)
