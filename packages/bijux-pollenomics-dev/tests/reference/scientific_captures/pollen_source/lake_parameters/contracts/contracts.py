"""Freeze source pages, owned imports and the separately observed source runtime."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from runtime_contracts import (
    namespace_snapshot,
    require_runtime_environment,
    verify_base_namespaces,
)
from source_admission import reviewed_controls, verify_namespace
from source_inputs import InputScope, exact_union, pin, verify_rows
from source_runtime import PYTHON as PYTHON
from source_runtime import SOURCE as SOURCE
from source_runtime import authenticate_runtime

ROOT = SOURCE.parents[2]
GIT = Path("/Library/Developer/CommandLineTools/usr/bin/git")
PACKAGES = (
    "bijux-pollenomics",
    "bijux-pollenomics-lra",
    "bijux-pollenomics-dev",
    "pollenomics",
)
MODULES = (
    "bijux_pollenomics",
    "bijux_pollenomics_lra",
    "bijux_pollenomics_dev",
    "pollenomics",
)


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "JSON object required")
    assert isinstance(value, dict)
    return value


def write(path: Path, value: object) -> None:
    require(not path.exists() and not path.is_symlink(), "Output replacement refused")
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        )


def identity() -> dict[str, str]:
    require_runtime_environment(dict(os.environ))

    def git(*args: str) -> bytes:
        return subprocess.check_output(
            [str(GIT), *args],
            cwd=ROOT,
            timeout=60,
            env=dict(
                os.environ,
                GIT_OPTIONAL_LOCKS="0",
                GIT_CONFIG_NOSYSTEM="1",
                GIT_CONFIG_GLOBAL=os.devnull,
            ),
        )

    require(
        git("branch", "--show-current").strip() == b"main", "Clean local main required"
    )
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def output_root(path: Path) -> Path:
    path = path.absolute()
    require(
        ".." not in path.parts
        and path != ROOT / "artifacts"
        and path.is_relative_to(ROOT / "artifacts")
        and path.resolve() == path
        and not path.exists()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Fresh normalized artifact output required",
    )
    return path


class LakeInputs(InputScope):
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        super().__init__(rows, [PYTHON, GIT])
        self.namespaces: list[dict[str, Any]] = []

    def capture_tree(self, root: Path) -> list[str]:
        require(
            not any(path.is_symlink() for path in (root, *root.parents)),
            "Input namespace has a lexical alias ancestor",
        )
        snapshot = namespace_snapshot(root, [])
        names = []
        for name, row in snapshot["entries"].items():
            require(row["kind"] != "symlink", "Owned input aliases refused")
            if row["kind"] == "file":
                path = root / name
                require(path.stat().st_nlink == 1, "Independent regular input required")
                names.append(str(path))
        self.capture(Path(name) for name in names)
        self.namespaces.append(snapshot)
        return sorted(names)

    def verify(self) -> None:
        super().verify()
        for row in self.namespaces:
            root = Path(row["root"])
            require(
                not any(path.is_symlink() for path in (root, *root.parents)),
                "Original input namespace alias ancestry changed",
            )
        verify_base_namespaces(self.namespaces)


def validate_private_namespace(
    root: Path, expected: list[dict[str, Any]]
) -> dict[str, Any]:
    require(
        not any(path.is_symlink() for path in (root, *root.parents)),
        "Private capture has a lexical alias ancestor",
    )
    names = [row["path"] for row in expected]
    require(
        len(names) == len(set(names)) == 28,
        "Exact28 private source identities required",
    )
    require(
        all(Path(name).is_relative_to(root) for name in names),
        "Private input leaves capture root",
    )
    snapshot = namespace_snapshot(root, [])
    actual = {
        str(root / name)
        for name, row in snapshot["entries"].items()
        if row["kind"] == "file"
    }
    require(actual == set(names), "Private source member set differs")
    require(
        all(
            row["kind"] in {"file", "directory"} for row in snapshot["entries"].values()
        ),
        "Private alias refused",
    )
    require(
        {
            name
            for name, row in snapshot["entries"].items()
            if row["kind"] == "directory"
        }
        == {"capture-pages"},
        "Unexpected private source directory",
    )
    verify_rows(expected)
    return snapshot


def checkpoint(authority: dict[str, Any], scope: LakeInputs) -> None:
    verify_namespace(SOURCE)
    scope.verify()
    current, _ = authenticate_runtime()
    require(current == authority, "Observed147 source runtime changed")
    scope.verify()
    verify_namespace(SOURCE)


def execution_scope(plan: dict[str, Any]) -> tuple[dict[str, Any], LakeInputs]:
    _, _, controlled = reviewed_controls(SOURCE)
    authority, _ = authenticate_runtime()
    require(authority == plan["qualified_source_runtime"], "Runtime authority differs")
    scope = LakeInputs(exact_union(plan["input_pins"], controlled))
    require(
        scope.rows == plan["input_pins"], "Reviewed source was not in original plan"
    )
    require(
        scope.aliases == plan["runtime_entry_raw_aliases"]
        and scope.entries == plan["runtime_entry_lexical_paths"],
        "Original raw launch aliases differ",
    )
    scope.namespaces = deepcopy(plan["input_namespace_snapshots"])
    checkpoint(authority, scope)
    return authority, scope


def bootstrap(plan: dict[str, Any]) -> list[dict[str, Any]]:
    import importlib

    require(
        Path(sys.executable).absolute() == PYTHON
        and sys.flags.isolated == 1
        and sys.flags.dont_write_bytecode == 1,
        "Qualified isolated lexical interpreter required",
    )
    roots = [ROOT / "packages" / name / "src" for name in PACKAGES]
    sys.path[:0] = list(map(str, roots))
    origins = []
    for name, root in zip(MODULES, roots, strict=True):
        module = importlib.import_module(name)
        filename = module.__file__
        require(
            isinstance(filename, str), "First-party module has no regular source origin"
        )
        assert isinstance(filename, str)
        path = Path(filename).absolute()
        require(
            path.is_relative_to(root)
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "First-party import escaped owned source",
        )
        origins.append({"module": name, **pin(path)})
    expected = {row["path"]: row for row in plan["input_pins"]}
    require(
        all(
            expected.get(row["path"])
            == {k: row[k] for k in ("path", "sha256", "bytes")}
            for row in origins
        ),
        "Imported first-party origin was not originally protected",
    )
    return origins
