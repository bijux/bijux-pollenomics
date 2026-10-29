"""Reject private-payload promotion and incomplete physical capsule membership."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.neotoma_lake.members import (
    validate_catalog,
    validate_members,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)
ARTIFACTS = ROOT / "artifacts/ci/neotoma-lake-capture-controls"


class MemberControls(unittest.TestCase):
    def test_complete_regular_members_and_special_entry_refusals(self) -> None:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        for case in (
            "positive",
            "missing",
            "extra",
            "FIFO",
            "alias",
            "directory_alias",
            "bytecode",
            "escape",
            "boolean_size",
        ):
            with tempfile.TemporaryDirectory(dir=ARTIFACTS) as folder:
                root = Path(folder)
                (root / "capture.json").write_text("{}\n")
                raw = b"first-party-source"
                (root / "source.py").write_bytes(raw)
                members: dict[str, Any] = {
                    "source.py": {
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw),
                    }
                }
                if case == "missing":
                    (root / "source.py").unlink()
                elif case == "extra":
                    (root / "extra.txt").write_text("extra")
                elif case == "FIFO":
                    os.mkfifo(root / "pipe")
                elif case == "alias":
                    (root / "alias.py").symlink_to("source.py")
                elif case == "directory_alias":
                    (root / "alias").symlink_to(root, target_is_directory=True)
                elif case == "bytecode":
                    (root / "source.py").rename(root / "source.pyc")
                    members["source.pyc"] = members.pop("source.py")
                elif case == "escape":
                    members["../source.py"] = members.pop("source.py")
                elif case == "boolean_size":
                    members["source.py"]["bytes"] = True
                if case == "positive":
                    validate_members(root, members)
                else:
                    with self.assertRaises(ReportRebuildError):
                        validate_members(root, members)

    def test_ordered_identity_roles_and_unreviewed_omission_refusals(self) -> None:
        paths = [
            "/repository/packages/example/src/module.py",
            "/private/source.json",
            "/repository/packages/example/src/__pycache__/module.pyc",
            "/runtime/stdlib.py",
        ]
        pins = [
            {"path": p, "sha256": str(i) * 64, "bytes": i + 1}
            for i, p in enumerate(paths)
        ]
        roles = [
            "public_first_party_source_or_resource",
            "private_source_identity_only",
            "bytecode_identity_only",
            "runtime_dependency_identity_only",
        ]
        catalog: list[dict[str, Any]] = [
            {
                **pin,
                "original_index": i,
                "retention_role": role,
                "retained_member": "source/module.py" if i == 0 else None,
            }
            for i, (pin, role) in enumerate(zip(pins, roles, strict=True))
        ]
        members = {
            "source/module.py": {key: pins[0][key] for key in ("sha256", "bytes")}
        }
        arguments: dict[str, Any] = {
            "private_root": "/private",
            "repository": "/repository",
            "public_paths": {paths[0]},
            "runtime_paths": {paths[3]},
        }
        counts = validate_catalog(catalog, pins, members, **arguments)
        self.assertEqual(sum(counts.values()), 4)
        for case in (
            "private_published",
            "unknown_runtime",
            "wrong_order",
            "boolean_index",
            "changed_hash",
            "duplicate_original",
        ):
            rows, original = deepcopy(catalog), deepcopy(pins)
            if case == "private_published":
                rows[1]["retention_role"] = "public_control_or_declared_metadata"
                rows[1]["retained_member"] = "source/module.py"
            elif case == "unknown_runtime":
                rows[1]["retention_role"] = "runtime_dependency_identity_only"
            elif case == "wrong_order":
                rows.reverse()
            elif case == "boolean_index":
                rows[0]["original_index"] = False
            elif case == "changed_hash":
                rows[0]["sha256"] = "f" * 64
            else:
                original[1] = original[0]
            with self.assertRaises(ReportRebuildError):
                validate_catalog(rows, original, members, **arguments)
