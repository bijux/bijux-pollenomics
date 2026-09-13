"""Private native-geometry audit with existing custody and no-replace publication."""

from __future__ import annotations

from hashlib import sha256
from importlib import metadata
from itertools import chain
import os
from pathlib import Path
import tempfile

import pyproj
from pyproj import datadir

from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from ..materialization.ownership import canonical_bytes
from ..materialization.reading import read_only_database
from .models import BOUNDARY, SCHEMA_VERSION, RaaGeometryAudit
from .rows import iter_geometry_documents


def implementation_identity() -> dict[str, str]:
    """Bind source helpers, publication and the CRS database used for validation."""
    owner = Path(__file__).resolve().parent
    package = owner.parents[3]
    paths = (
        set(owner.glob("*.py"))
        | set((owner.parent / "materialization").glob("*.py"))
        | {package / "core/owned_tree.py"}
    )
    for parent in (owner, *owner.parents):
        if parent == package.parent:
            break
        initializer = parent / "__init__.py"
        if initializer.is_file():
            paths.add(initializer)
    result = {
        path.relative_to(package).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }
    result.update(
        {
            "dependency:pyproj_version": metadata.version("pyproj"),
            "dependency:proj_version": pyproj.proj_version_str,
            "dependency:proj_database_sha256": sha256(
                (Path(datadir.get_data_dir()) / "proj.db").read_bytes()
            ).hexdigest(),
        }
    )
    return result


def _paths(source_path: Path, destination: Path) -> tuple[Path, Path]:
    for path in (source_path, *source_path.parents, destination, *destination.parents):
        if path.is_symlink():
            raise ValueError("RAÄ geometry audit paths cannot use symlinks")
    source, output = (
        Path(os.path.abspath(source_path)),
        Path(os.path.abspath(destination)),
    )
    for path in (source, *source.parents, output, *output.parents):
        if path.is_symlink():
            raise ValueError("RAÄ geometry audit paths cannot use symlinks")
    if output.is_relative_to(source.parent) or source.parent.is_relative_to(output):
        raise ValueError("RAÄ geometry audit must not overlap source capture")
    if output.exists():
        raise FileExistsError(output)
    return source, output


def audit_raa_geometry(
    source_path: Path,
    *,
    expected_sha256: str,
    expected_byte_count: int,
    destination: Path,
) -> RaaGeometryAudit:
    """Audit structure/declared CRS only; preserve every invalid/empty occurrence."""
    source, output = _paths(source_path, destination)
    implementation = implementation_identity()
    digest = sha256()
    count = size = 0
    summary: dict[str, object] | None = None
    with read_only_database(
        source, expected_sha256=expected_sha256, expected_byte_count=expected_byte_count
    ) as connection:
        documents = iter_geometry_documents(connection)
        first = next(documents)  # Source-profile refusal precedes staging writes.
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".raa-geometry-", dir=output.parent))
        with (staging / "geometry.ndjson").open("xb") as stream:
            for record in chain((first,), documents):
                content = canonical_bytes(record)
                stream.write(content)
                digest.update(content)
                size += len(content)
                count += 1
                if record["kind"] == "summary":
                    summary = record
            stream.flush()
            os.fsync(stream.fileno())
    if summary is None or implementation_identity() != implementation:
        raise ValueError("RAÄ geometry producer or summary changed")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source": {"sha256": expected_sha256, "byte_count": expected_byte_count},
        "boundary": BOUNDARY,
        "implementation": implementation,
        "files": {
            "geometry.ndjson": {
                "sha256": digest.hexdigest(),
                "byte_count": size,
                "record_count": count,
            }
        },
        "summary": summary,
    }
    content = canonical_bytes(manifest)
    with (staging / "manifest.json").open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    publish_new_output_tree(final_output_root=output, staging_output_root=staging)
    return RaaGeometryAudit(output, sha256(content).hexdigest(), content.decode())
