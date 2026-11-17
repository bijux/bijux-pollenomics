"""Publish private native UUID dispositions and sparse conditional registry counts."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import asdict
from hashlib import sha256
import os
from pathlib import Path
import secrets
import sys
from typing import Any, cast

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note
from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    publish_owned_replacement,
    read_regular_file,
)
from bijux_pollenomics.core.filesystem.recovery_storage import (
    resolve_publication_workspace_parent,
)

from ..materialization.custody import SourceConnection
from ..materialization.ownership import canonical_bytes
from ..materialization.reading import read_only_database
from .contracts import (
    BOUNDARY,
    SCHEMA_VERSION,
    NativePointGridLimits,
    RaaNativePointGrid,
)
from .projection import GRID, NativePointProjection
from .rows import iter_point_grid_documents


class _Candidate:
    """Keep the original destination parent inside the existing publication seal."""

    def __init__(self, writer: OwnedTreeWriter, parent: DirectoryAnchor) -> None:
        self.writer, self.parent, self.root = writer, parent, writer.root

    def validate_attachment(self) -> None:
        """Refuse a changed destination before the core owner may attach a tree."""
        self.parent.check()
        self.writer.validate_attachment()
        self.parent.check()

    def validate_closed_attachment(self, root: Path) -> None:
        """Seal the exact completed private namespace at either authorized name."""
        self.parent.check()
        self.writer.validate_closed_attachment(root)
        self.parent.check()


def _implementation() -> dict[str, object]:
    owner = Path(__file__).absolute().parent
    package = owner.parents[3]
    paths = set(owner.glob("*.py"))
    paths.update(
        owner.parent / "materialization" / name
        for name in ("reading.py", "contracts.py", "custody.py", "ownership.py")
    )
    paths.update(
        owner.parent / "geometry" / name
        for name in ("binary.py", "crs.py", "rows.py", "models.py")
    )
    paths.update(
        package / "core/filesystem" / name
        for name in (
            "anchors.py",
            "owned_writes.py",
            "replacement.py",
            "regular_inputs.py",
            "namespaces.py",
            "recovery_storage.py",
        )
    )
    return {
        "python": sys.version,
        "files": {
            str(path.relative_to(package)): sha256(
                read_regular_file(path, max_bytes=1024**2)
            ).hexdigest()
            for path in sorted(paths)
        },
    }


def _paths(source: Path, destination: Path) -> tuple[Path, Path]:
    for path in (source, *source.parents, destination, *destination.parents):
        if path.is_symlink():
            raise ValueError("Native POINT paths cannot use aliases")
    source, destination = source.absolute(), destination.absolute()
    if source.parent.is_relative_to(destination) or destination.is_relative_to(
        source.parent
    ):
        raise ValueError("Native POINT output must not overlap source capture")
    if os.path.lexists(destination):
        raise FileExistsError(destination)
    return source, destination


def _write_product(
    output: Path,
    parent: DirectoryAnchor,
    buffers: dict[str, bytes],
    limits: NativePointGridLimits,
    check_implementation: Callable[[], None],
) -> RaaNativePointGrid:
    storage_path = resolve_publication_workspace_parent(
        output, namespace="raa-point-grid"
    )
    with ExitStack() as stack:
        storage = stack.enter_context(DirectoryAnchor(storage_path, create=True))
        parent.check()
        name = "publication-" + secrets.token_hex(16)
        os.mkdir(name, 0o700, dir_fd=storage.fd)
        recovery = stack.enter_context(DirectoryAnchor(storage.path / name))
        writer = stack.enter_context(
            OwnedTreeWriter(
                recovery.path / "candidate",
                max_bytes=limits.max_output_bytes,
                max_files=3,
            )
        )
        try:
            with DirectoryAnchor(writer.root) as private:
                os.fchmod(private.fd, 0o700)
                private.check()
            for member, body in buffers.items():
                parent.check()
                writer.write_bytes(member, body)
            expected = {
                member: sha256(body).hexdigest() for member, body in buffers.items()
            }

            def validate(root: Path) -> None:
                parent.check()
                check_implementation()
                with BoundedInputTree(
                    root, max_bytes=limits.max_output_bytes, max_files=3
                ) as tree:
                    if set(tree.files) != set(buffers):
                        raise ValueError(
                            "Native POINT publication file membership changed"
                        )
                    tree.validate()
                    if tree.digests != expected:
                        raise ValueError("Native POINT publication bytes changed")
                parent.check()

            publish_owned_replacement(
                _Candidate(writer, parent),
                final=output,
                prior=None,
                recovery=recovery,
                validate=validate,
            )
            parent.check()
            return RaaNativePointGrid(
                output, expected["report.json"], buffers["report.json"].decode()
            )
        except BaseException as error:
            add_cleanup_note(
                error,
                lambda: (
                    f"Private native POINT publication evidence retained at {recovery.path}"
                ),
            )
            raise


def materialize_raa_native_point_grid(
    source_path: Path,
    *,
    expected_sha256: str,
    expected_byte_count: int,
    destination: Path,
    limits: NativePointGridLimits,
) -> RaaNativePointGrid:
    """Count conditional native registry UUIDs; never infer archaeological events."""
    if not isinstance(limits, NativePointGridLimits):
        raise ValueError("Native POINT publication requires explicit finite limits")
    source, output = _paths(Path(source_path), Path(destination))
    with DirectoryAnchor(output.parent, create=True) as parent:
        implementation = _implementation()
        projection = NativePointProjection()
        projection_identity = projection.identity()
        ledger = bytearray()
        profile: dict[str, object] | None = None
        summary: dict[str, Any] | None = None
        with read_only_database(
            source,
            expected_sha256=expected_sha256,
            expected_byte_count=expected_byte_count,
        ) as connection:
            for record in iter_point_grid_documents(connection, limits, projection):
                if record["kind"] == "profile":
                    profile = record
                elif record["kind"] == "summary":
                    summary = record
                else:
                    body = canonical_bytes(record)
                    if len(ledger) + len(body) > limits.max_output_bytes:
                        raise ValueError(
                            "Native POINT ledger exceeds output byte budget"
                        )
                    ledger.extend(body)
            parent.check()
            if profile is None or summary is None:
                raise ValueError(
                    "Native POINT source did not produce complete conservation"
                )
            cells = "west_longitude,south_latitude,uuid_count\n" + "".join(
                f"{row['west_longitude']},{row['south_latitude']},{row['uuid_count']}\n"
                for row in summary.pop("cells")
            )
            buffers = {
                "uuid-dispositions.ndjson": bytes(ledger),
                "cell-counts.csv": cells.encode("ascii"),
            }
            del ledger
            report = {
                "schema_version": SCHEMA_VERSION,
                "source": {
                    "sha256": expected_sha256,
                    "byte_count": expected_byte_count,
                },
                "native_profile_sha256": profile["native_profile_sha256"],
                "source_CRS": profile["crs"],
                "selection": {
                    "native_owner": "lamning.uuid",
                    "native_class_field": "antikvariskbedomning",
                    "native_class_value": "Fornlämning",
                    "raw_primary_point_occurrences": 1,
                    "valid_primary_point_occurrences": 1,
                    "uncertainty_role": "separately_counted_never_selected",
                    "disposition_precedence": list(summary["dispositions"]),
                },
                "grid": GRID,
                "projection": projection_identity,
                "boundary": BOUNDARY,
                "implementation": implementation,
                "limits": asdict(limits),
                "counts": summary["counts"],
                "dispositions": summary["dispositions"],
                "geometry_role_rows": summary["geometry_role_rows"],
                "cell_count_total": summary["cell_count_total"],
                "files": {
                    name: {"sha256": sha256(body).hexdigest(), "byte_count": len(body)}
                    for name, body in buffers.items()
                },
                "public_shareable_surface": "aggregate_counts_and_provenance_only; UUID ledger and coordinates remain private",
            }
            buffers["report.json"] = canonical_bytes(report)
            if sum(map(len, buffers.values())) > limits.max_output_bytes:
                raise ValueError("Native POINT product exceeds output byte budget")

            def check_implementation() -> None:
                cast(SourceConnection, connection).check_source()
                if (
                    _implementation() != implementation
                    or projection.identity() != projection_identity
                ):
                    raise ValueError(
                        "Native POINT implementation or projection changed"
                    )

            check_implementation()
            return _write_product(output, parent, buffers, limits, check_implementation)
