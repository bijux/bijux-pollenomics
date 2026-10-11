"""Expose reviewed scientific PDFs without copying them into the source tree."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "reports/exports/site-downloads.json"
DECKS = ("big-picture", "developer", "scientific-evidence")


def _read(root: Path, relative: str) -> bytes:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError(f"Unsafe scientific download path: {relative}")
    source = root / relative
    if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Scientific download source unavailable: {relative}")
    return source.read_bytes()


def download_bytes(root: Path) -> dict[str, bytes]:
    """Validate the exact population and freeze its bytes before site rendering."""
    manifest = json.loads(_read(root, MANIFEST))
    if manifest.get("schema_version") != "scientific-reader-downloads.v1":
        raise ValueError("Unknown scientific download manifest")
    inventory = list(
        csv.DictReader(
            _read(root, "reports/science/paper-accounts.csv").decode().splitlines()
        )
    )
    expected = {
        f"reports/exports/papers/{row['paper_id']}.pdf": (
            f"assets/science/papers/{row['paper_id']}.pdf",
            row["canonical_report"],
        )
        for row in inventory
    }
    expected.update(
        {
            f"presentation/{name}.pdf": (
                f"assets/science/presentations/{name}.pdf",
                f"presentation/{name}.tex",
            )
            for name in DECKS
        }
    )
    rows = manifest["files"]
    if len(inventory) != 9 or len(rows) != 12 or len(expected) != 12:
        raise ValueError("Scientific download population changed")
    if {row["path"] for row in rows} != set(expected):
        raise ValueError("Scientific download membership differs")
    for relative, digest in manifest["inputs"].items():
        if hashlib.sha256(_read(root, relative)).hexdigest() != digest:
            raise ValueError(f"Scientific download input changed: {relative}")
    required_inputs = {
        "reports/science/paper-accounts.csv",
        "reports/exports/papers/manifest.json",
        "reports/exports/papers/visual-review.json",
        "presentation/source-lock.json",
    }
    if not required_inputs <= set(manifest["inputs"]):
        raise ValueError("Scientific download input closure incomplete")
    deck_lock = json.loads(_read(root, "presentation/source-lock.json"))
    if deck_lock["decks"] != list(DECKS):
        raise ValueError("Scientific download deck identity differs")
    for relative, digest in deck_lock["sources"].items():
        if hashlib.sha256(_read(root, relative)).hexdigest() != digest:
            raise ValueError(f"Scientific download deck source changed: {relative}")
    frozen = {}
    for row in rows:
        uri, source = expected[row["path"]]
        if row["site_uri"] != uri or row["canonical_source"] != source:
            raise ValueError("Scientific download route or canonical source differs")
        content = _read(root, row["path"])
        if (
            not content.startswith(b"%PDF-")
            or len(content) != row["bytes"]
            or hashlib.sha256(content).hexdigest() != row["sha256"]
            or hashlib.sha256(_read(root, source)).hexdigest() != row["source_sha256"]
        ):
            raise ValueError(f"Scientific download identity changed: {row['path']}")
        frozen[uri] = content
    return frozen


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Require canonical export verification before inserting virtual PDF files."""
    runpy.run_path(str(ROOT / "reports/exports/papers/verify.py"), run_name="__main__")
    frozen = download_bytes(ROOT)
    if set(frozen) & {file.src_uri for file in files}:
        raise ValueError("Scientific download route collides with a docs source")
    for uri, content in frozen.items():
        files.append(File.generated(config, uri, content=content))
    return files
