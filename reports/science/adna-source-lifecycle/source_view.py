"""Prepare exact retained logical input bytes below an owned artifact directory."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def input_path(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or not rel.parts
        or rel.parts[0] not in {"data", "docs", "reports"}
    ):
        raise ValueError("Input path escaped declared source scope")
    path = root / rel
    if any(
        parent.is_symlink()
        for parent in [path, *path.parents]
        if parent.is_relative_to(root)
    ):
        raise ValueError("Symlink input refused")
    return path


def prepare(root: Path, output: Path, manifest: Path) -> None:
    root = root.resolve()
    if ".." in output.parts or any(p.is_symlink() for p in [output, *output.parents]):
        raise ValueError("Ambiguous output refused")
    output = output.resolve()
    if (
        not output.is_relative_to(root / "artifacts")
        or output == root / "artifacts"
        or output.exists()
    ):
        raise ValueError("Choose a new owned artifact directory")
    payload: dict[str, Any] = json.loads(manifest.read_text())
    declared = {row["path"]: row for row in payload["inputs"]}
    if (
        len(declared) != len(payload["inputs"])
        or sum(row["bytes"] for row in declared.values()) > 100 * 1024**2
    ):
        raise ValueError("Input population/work bound refused")
    output.mkdir(parents=True)
    for relative, row in declared.items():
        path = input_path(root, relative)
        if path.is_file():
            content = path.read_bytes()
        else:
            storage_rel = relative + ".gz"
            metadata_rel = relative + ".metadata.json"
            if storage_rel not in declared or metadata_rel not in declared:
                raise ValueError("Missing declared source transport")
            storage = input_path(root, storage_rel).read_bytes()
            metadata = input_path(root, metadata_rel).read_bytes()
            if (
                digest(storage) != declared[storage_rel]["sha256"]
                or digest(metadata) != declared[metadata_rel]["sha256"]
            ):
                raise ValueError("Source transport digest differs")
            info = json.loads(metadata)
            if (
                info["content_encoding"] != "gzip"
                or info["byte_size"] != row["bytes"]
                or info["storage_byte_size"] != len(storage)
                or row["bytes"] > 2 * 1024**2
            ):
                raise ValueError("Source transport size/encoding differs")
            with gzip.GzipFile(fileobj=io.BytesIO(storage)) as stream:
                content = stream.read(row["bytes"] + 1)
        if len(content) != row["bytes"] or digest(content) != row["sha256"]:
            raise ValueError("Source input byte identity differs")
        target = input_path(output, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(
        args.repository, args.output, Path(__file__).with_name("source-inputs.json")
    )


if __name__ == "__main__":
    main()
