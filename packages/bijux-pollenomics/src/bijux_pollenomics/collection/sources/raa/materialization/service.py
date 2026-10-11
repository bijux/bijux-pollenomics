"""Private, no-replace publication of a source-owned RAÄ row audit."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import tempfile

from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .contracts import BOUNDARY, SCHEMA_VERSION
from .ownership import canonical_bytes, iter_audit_documents
from .reading import read_only_database


def implementation_identity() -> dict[str, str]:
    """Bind the complete source-owned producer and shared publication primitive."""
    owner = Path(__file__).resolve().parent
    package = owner.parents[3]
    paths = set(owner.glob("*.py")) | {package / "core/owned_tree.py"}
    for parent in (owner, *owner.parents):
        if parent == package.parent:
            break
        initializer = parent / "__init__.py"
        if initializer.is_file():
            paths.add(initializer)
    return {
        path.relative_to(package).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def audit_raa_geopackage(
    source_path: Path,
    *,
    expected_sha256: str,
    expected_byte_count: int,
    output_directory: Path,
) -> dict[str, object]:
    """Audit raw row ownership only; do not admit geometry, chronology or density."""
    for path in (
        source_path,
        *source_path.parents,
        output_directory,
        *output_directory.parents,
    ):
        if path.is_symlink():
            raise ValueError("RAÄ audit paths cannot use symlinks")
    source = Path(os.path.abspath(source_path))
    output = Path(os.path.abspath(output_directory))
    for path in (source, *source.parents, output, *output.parents):
        if path.is_symlink():
            raise ValueError("RAÄ audit paths cannot use symlinks")
    if output.is_relative_to(source.parent) or source.parent.is_relative_to(output):
        raise ValueError("RAÄ audit output must not overlap source capture")
    if output.exists():
        raise FileExistsError(output)
    implementation = implementation_identity()
    # Input admission precedes even creation of a staging directory.
    with read_only_database(
        source, expected_sha256=expected_sha256, expected_byte_count=expected_byte_count
    ) as connection:
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".raa-audit-", dir=output.parent))
        digest = sha256()
        count = size = 0
        summary: dict[str, object] | None = None
        with (staging / "rows.ndjson").open("xb") as stream:
            for record in iter_audit_documents(connection):
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
        raise ValueError("RAÄ audit source producer or summary changed")
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "boundary": BOUNDARY,
        "source": {"sha256": expected_sha256, "byte_count": expected_byte_count},
        "implementation": implementation,
        "files": {
            "rows.ndjson": {
                "sha256": digest.hexdigest(),
                "byte_count": size,
                "record_count": count,
            }
        },
        "summary": summary,
    }
    with (staging / "manifest.json").open("xb") as stream:
        stream.write(canonical_bytes(manifest))
        stream.flush()
        os.fsync(stream.fileno())
    publish_new_output_tree(final_output_root=output, staging_output_root=staging)
    return manifest
