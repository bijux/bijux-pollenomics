"""Streaming table serialization and exclusive AADR bundle publication helpers."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import ExitStack
from hashlib import sha256
import os
from pathlib import Path
import tempfile

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.contracts import (
    MEMBER_FILES,
    canonical_bytes,
)


def new_staging(output_root: Path, *, data_root: Path) -> tuple[Path, Path]:
    """Reserve an isolated output sibling after overlap/symlink refusal."""
    for path in (output_root, *output_root.parents, data_root, *data_root.parents):
        if path.is_symlink():
            raise ValueError("AADR member path cannot use symlinks")
    output = Path(os.path.abspath(output_root))
    source = Path(os.path.abspath(data_root))
    for path in (output, *output.parents, source, *source.parents):
        if path.is_symlink():
            raise ValueError("AADR member path cannot use symlinks")
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("AADR private member output must not overlap source data")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output, Path(tempfile.mkdtemp(prefix=".aadr-members-", dir=output.parent))


def write_tables(
    directory: Path, documents: Iterable[tuple[str, dict[str, object]]]
) -> dict[str, object]:
    """Stream each source row once into its declared deterministic member file."""
    hashes = {name: sha256() for name in MEMBER_FILES}
    sizes = dict.fromkeys(MEMBER_FILES, 0)
    counts = dict.fromkeys(MEMBER_FILES, 0)
    with ExitStack() as stack:
        streams = {
            name: stack.enter_context((directory / name).open("xb"))
            for name in MEMBER_FILES
        }
        for name, record in documents:
            content = canonical_bytes(record)
            streams[name].write(content)
            hashes[name].update(content)
            sizes[name] += len(content)
            counts[name] += 1
    return {
        name: {
            "sha256": hashes[name].hexdigest(),
            "byte_count": sizes[name],
            "record_count": counts[name],
        }
        for name in MEMBER_FILES
    }


def implementation_identity() -> dict[str, str]:
    """Bind source-owned input/reconciliation/publication implementation bytes."""
    package = Path(__file__).resolve().parents[5]
    roots = [
        package / "adna/species/homo_sapiens/materialization",
        package / "collection/sources/aadr/materialization",
    ]
    paths = {p for root in roots for p in root.rglob("*.py")}
    paths.update(
        package / rel
        for rel in [
            "adna/species/homo_sapiens/release_manifest.py",
            "adna/species/homo_sapiens/text.py",
            "core/owned_tree.py",
        ]
    )
    for root in roots:
        for parent in (root, *root.parents):
            if parent == package.parent:
                break
            init = parent / "__init__.py"
            if init.is_file():
                paths.add(init)
    return {
        p.relative_to(package).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }
