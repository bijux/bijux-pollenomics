"""Resolve only independently reviewed controller code in the qualified source runtime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import sys

SOURCE = Path(__file__).resolve().parent


def _verify_entry_namespace(root: Path) -> None:
    expected = {
        ".": [
            "check_controls.py",
            "check_tools.py",
            "common_runner.py",
            "contracts.py",
            "execute_projection.py",
            "execute_reader.py",
            "lake_review.py",
            "observe.py",
            "prepare.py",
            "projection_review.py",
            "run.py",
            "runtime_contracts.py",
            "source_admission.py",
            "source_entry.py",
            "source_inputs.py",
            "source_runtime.py",
        ]
    }
    for domain, names in expected.items():
        directory = root if domain == "." else root / domain
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Controller import domain is absent or linked")
        for entry in directory.iterdir():
            if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
                raise ValueError("Controller import namespace contains alias/special")
            if domain == ".":
                if entry.is_dir() and entry.name not in {
                    "preflight",
                    *set(expected) - {"."},
                }:
                    raise ValueError("Unexpected controller import directory")
                if (
                    entry.suffix in {".py", ".pyc", ".so", ".pyd", ".dylib"}
                    and entry.name not in names
                ):
                    raise ValueError("Unexpected controller import member")
            elif entry.is_dir() or entry.name not in names:
                raise ValueError("Unexpected nested controller import member")
        if domain != "." and {entry.name for entry in directory.iterdir()} != set(
            names
        ):
            raise ValueError("Nested controller import member is missing")


def _verify_reviewed_entry(root: Path) -> None:
    manifest = root / "prepared-source-manifest.json"
    review = root / "independent-source-review.json"
    for path in (manifest, review):
        if not path.is_file() or any(
            parent.is_symlink() for parent in (path, *path.parents)
        ):
            raise ValueError(
                "Reviewed controller entry requires regular source authority"
            )
    raw = manifest.read_bytes()
    document = json.loads(raw)
    admission = json.loads(review.read_bytes())
    if (
        document["source_only"] is not True
        or admission["approved"] is not True
        or admission["source_manifest_sha256"] != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError(
            "Exact independent source approval required before local imports"
        )
    names = [row["path"] for row in document["files"]]
    if names != sorted(set(names)):
        raise ValueError("Reviewed entry source paths must be sorted and unique")
    for row in document["files"]:
        path = Path(row["path"])
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(root)
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError("Reviewed controller entry leaves physical source")
        if (
            not path.is_file()
            or type(row["bytes"]) is not int
            or path.stat().st_size != row["bytes"]
        ):
            raise ValueError("Reviewed controller entry length changed")
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        if checksum != row["sha256"]:
            raise ValueError("Reviewed controller source changed before local imports")
    required = {
        entry
        for names in {
            ".": [
                "check_controls.py",
                "check_tools.py",
                "common_runner.py",
                "contracts.py",
                "execute_projection.py",
                "execute_reader.py",
                "lake_review.py",
                "observe.py",
                "prepare.py",
                "projection_review.py",
                "run.py",
                "runtime_contracts.py",
                "source_admission.py",
                "source_entry.py",
                "source_inputs.py",
                "source_runtime.py",
            ]
        }.values()
        for entry in names
    }
    declared = {Path(name).relative_to(root).as_posix() for name in names}
    if not required.issubset(declared):
        raise ValueError("Reviewed controller manifest omits a local import member")


_verify_entry_namespace(Path(__file__).resolve().parent)
_verify_reviewed_entry(Path(__file__).resolve().parent)
sys.path.insert(0, str(SOURCE))
from source_admission import reviewed_controls, verify_namespace  # noqa: E402
from source_inputs import verify_rows  # noqa: E402
from source_runtime import authenticate_runtime  # noqa: E402 - guarded local namespace.


def main() -> None:
    if len(sys.argv) < 2:
        raise ValueError("An explicit source controller is required")
    target = SOURCE / sys.argv[1]
    if target.parent != SOURCE or target.name not in {
        "prepare.py",
        "execute_reader.py",
        "execute_projection.py",
        "run.py",
        "observe.py",
    }:
        raise ValueError("Unreviewed source controller entrypoint")
    _, _, reviewed_rows = reviewed_controls(SOURCE)
    before, _ = authenticate_runtime()
    argv = list(sys.argv)
    try:
        sys.argv = [str(target), *argv[2:]]
        verify_namespace(SOURCE)
        verify_rows(reviewed_rows)
        runpy.run_path(str(target), run_name="__main__")
    finally:
        sys.argv = argv
        verify_namespace(SOURCE)
        verify_rows(reviewed_rows)
        after, _ = authenticate_runtime()
        if after != before:
            raise ValueError("Qualified source runtime changed during controller entry")


if __name__ == "__main__":
    main()
