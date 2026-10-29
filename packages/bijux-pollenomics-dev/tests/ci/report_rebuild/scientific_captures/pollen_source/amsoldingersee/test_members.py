"""Refuse content-member escapes and silent source-payload omission changes."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import os
from pathlib import Path
import tempfile
from typing import Any
import unittest


@contextmanager
def fixture(parent: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    with tempfile.TemporaryDirectory(
        dir=parent, prefix="amsoldingersee-member-"
    ) as directory:
        root = Path(directory)
        (root / "members").mkdir()
        body = b"original public source\n"
        digest = hashlib.sha256(body).hexdigest()
        (root / "members" / digest).write_bytes(body)
        (root / "capture.json").write_text("{}\n")
        yield root, {"members/" + digest: {"sha256": digest, "bytes": len(body)}}


def boundary_checks(module: Any, parent: Path) -> int:
    with fixture(parent) as (root, members):
        module.namespace(root, members)
        for name, kind in (
            ("unlisted", "file"),
            ("empty", "dir"),
            ("fifo", "fifo"),
            ("alias", "alias"),
        ):
            path = root / name
            if kind == "file":
                path.write_bytes(b"unknown")
            elif kind == "dir":
                path.mkdir()
            elif kind == "fifo":
                os.mkfifo(path)
            else:
                path.symlink_to(root / "capture.json")
            try:
                module.namespace(root, members)
            except ValueError:
                pass
            else:
                raise AssertionError("Unlisted physical entry accepted: " + kind)
            if kind == "dir":
                path.rmdir()
            else:
                path.unlink()
        row = next(iter(members.values()))
        for unsafe in ("", "."):
            try:
                module.namespace(root, {unsafe: row})
            except ValueError:
                pass
            else:
                raise AssertionError("Empty/dot content name accepted")
        row["bytes"] = True
        try:
            module.namespace(root, members)
        except ValueError:
            return 7
        raise AssertionError("Boolean member byte size accepted")


def catalog_checks(module: Any, parent: Path) -> int:
    repository = "/controlled/repository"
    output = (
        repository + "/artifacts/science/current-amsoldingersee-source-refusal-replay"
    )
    members: dict[str, Any] = {}

    def member(text: str) -> str:
        body = text.encode()
        digest = hashlib.sha256(body).hexdigest()
        name = "members/" + digest
        members[name] = {"sha256": digest, "bytes": len(body)}
        return name

    values = [
        (repository + "/packages/bijux-pollenomics-dev/src/module.py", "public_source"),
        (
            repository + "/packages/bijux-pollenomics-dev/src/__pycache__/module.pyc",
            "bytecode_identity_only",
        ),
        ("/Users/bijan/bijux/-bijux-pollenomics-data/input", "private_identity_only"),
        ("/qualified/runtime", "runtime_identity_only"),
        (repository + "/configs/ci/report-ownership.json", "public_control"),
    ]
    rows = []
    roles = []
    for name, kind in values:
        key = member(name) if kind.startswith("public_") else None
        row = {
            "path": name,
            **(members[key] if key is not None else {"sha256": "a" * 64, "bytes": 3}),
        }
        rows.append(row)
        roles.append({"role": kind, "member": key})
    result_key = member("native result")
    ref_key = member("native reference")
    result = {"path": output + "/result.json", **members[result_key]}
    reference = {"path": output + "/plan.json", **members[ref_key]}
    jobs = {
        "production": {
            "plan.json": {
                "repository": repository,
                "output": output,
                "input_pins": rows,
            },
            "terminal.json": {"products": [result]},
        }
    }
    capture: dict[str, Any] = {
        "members": members,
        "input_roles": {"production": roles},
        "role_counts": {"production": dict(Counter(kind for _, kind in values))},
        "jobs": {"production": {"plan.json": ref_key}},
        "public_results": [
            {"original": result, "member": result_key},
            {"original": reference, "member": ref_key},
        ],
        "private_runtime_bytecode_payloads_copied": False,
        "bytecode_source_equivalence_claimed": False,
    }
    module.catalogs(parent, capture, jobs)
    for kind in (
        "source_role",
        "omitted_payload",
        "count",
        "missing_result",
        "duplicate_result",
        "unbound_member",
        "bytecode_claim",
    ):
        changed = deepcopy(capture)
        if kind == "source_role":
            changed["input_roles"]["production"][0]["role"] = "public_control"
        elif kind == "omitted_payload":
            changed["input_roles"]["production"][1]["member"] = result_key
        elif kind == "count":
            changed["role_counts"]["production"]["public_source"] = True
        elif kind == "missing_result":
            changed["public_results"].pop()
        elif kind == "duplicate_result":
            changed["public_results"].append(changed["public_results"][0])
        elif kind == "unbound_member":
            changed["members"]["members/" + "b" * 64] = {"sha256": "b" * 64, "bytes": 1}
        else:
            changed["bytecode_source_equivalence_claimed"] = True
        try:
            module.catalogs(parent, changed, jobs)
        except ValueError:
            continue
        raise AssertionError(
            "Original input/result partition inflation accepted: " + kind
        )
    return 7


class MemberBoundary(unittest.TestCase):
    def test_unlisted_alias_special_and_directory_entries_refuse(self) -> None:
        members = importlib.import_module(
            "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.amsoldingersee.members"
        )

        root = next(
            parent
            for parent in Path(__file__).resolve().parents
            if (parent / "pyproject.toml").is_file()
            and (parent / "configs/pytest.ini").is_file()
        )
        artifacts = root / "artifacts/science/amsoldingersee-canonical-source-guards"
        artifacts.mkdir(parents=True, exist_ok=True)
        self.assertEqual(boundary_checks(members, artifacts), 7)
        self.assertEqual(catalog_checks(members, artifacts), 7)


if __name__ == "__main__":
    unittest.main()
