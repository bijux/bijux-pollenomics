"""Admit current scientific decks from actual compiled input Git identities."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import re
from typing import Any

DECKS = ("big-picture", "developer", "scientific-evidence")
COMPILED_INPUTS = (
    *(f"presentation/{name}.tex" for name in DECKS),
    "presentation/shared.tex",
    "presentation/build.py",
)
FLAGS = (
    "-pdf",
    "-g",
    "-recorder",
    "-interaction=nonstopmode",
    "-halt-on-error",
    "-file-line-error",
)


def admitted_sources(
    root: Path,
    manifest: dict[str, Any],
    read: Callable[[Path, str], bytes],
    committed: Callable[[Path, str, list[str]], dict[str, bytes]],
    git: Callable[..., bytes],
) -> dict[str, Any]:
    """Bind only compiled TeX/shared/build tools; cited evidence has other owners.

    A successful compiler result is not scientific approval, readable rendering,
    font portability, citation availability or human review. Those acceptance
    checks remain separate. Historical source locks and export contexts are not
    rewritten or interpreted as the source of these newly compiled PDFs.
    """
    build = manifest["deck_build"]
    if (
        not isinstance(build, dict)
        or set(build)
        != {
            "schema_version",
            "source_revision",
            "source_date_epoch",
            "inputs",
            "compilers",
        }
        or build["schema_version"] != "git-compiled-deck-inputs.v1"
        or not isinstance(build["source_revision"], str)
        or re.fullmatch("[0-9a-f]{40}", build["source_revision"]) is None
        or type(build["source_date_epoch"]) is not int
        or build["source_date_epoch"] < 0
        or build["inputs"] != list(COMPILED_INPUTS)
        or not isinstance(build["compilers"], list)
        or len(build["compilers"]) != 3
    ):
        raise ValueError("Compiled deck Git identity differs")
    for name, row in zip(DECKS, build["compilers"], strict=True):
        if (
            not isinstance(row, dict)
            or set(row) != {"deck", "argv", "actual_exit"}
            or row["deck"] != name
            or type(row["actual_exit"]) is not int
            or row["actual_exit"] != 0
            or row["argv"]
            != [
                "latexmk",
                *FLAGS,
                f"-outdir=artifacts/jobs/presentation/{name}",
                f"presentation/{name}.tex",
            ]
        ):
            raise ValueError("Compiled deck actual compiler completion differs")
    stale = {
        "presentation/source-lock.json",
        "presentation/retained-source-context.json",
        "presentation/retained-build-source-context.json",
        "presentation/current-build-export-context.json",
        "configs/docs/publication/deck_exports.py",
    }
    if stale & set(manifest["inputs"]):
        raise ValueError("Current decks cannot use historical inventory hash triggers")
    decks = [
        row for row in manifest["files"] if row["path"].startswith("presentation/")
    ]
    if len(decks) != 3 or any("source_sha256" in row for row in decks):
        raise ValueError("Current deck sources must use their build Git revision")
    revision = build["source_revision"]
    git(root, "merge-base", "--is-ancestor", revision, "HEAD")
    epoch = int(git(root, "show", "-s", "--format=%ct", revision))
    if epoch != build["source_date_epoch"]:
        raise ValueError("Compiled deck source date epoch differs")
    paths = list(COMPILED_INPUTS)
    original = committed(root, revision, paths)
    current_revision = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    current = committed(root, current_revision, paths)
    modes = git(root, "ls-tree", "-r", "-z", current_revision, "--", *paths)
    for record in modes.split(b"\0"):
        if record:
            metadata, encoded = record.split(b"\t", 1)
            physical_path = root / encoded.decode()
            physical = b"100755" if physical_path.stat().st_mode & 0o100 else b"100644"
            if metadata.split()[0] != physical:
                raise ValueError("Compiled deck physical source mode differs")
    for path in paths:
        if original[path] != current[path] or current[path] != read(root, path):
            raise ValueError("Compiled deck input changed: " + path)
    final_revision = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    final = committed(root, final_revision, paths)
    git(root, "merge-base", "--is-ancestor", revision, "HEAD")
    for path in paths:
        if final[path] != original[path] or read(root, path) != original[path]:
            raise ValueError("Compiled deck input changed during validation: " + path)
    return {
        "context": build,
        "current_inputs": [
            {"path": path, "source_revision": revision} for path in paths
        ],
    }
